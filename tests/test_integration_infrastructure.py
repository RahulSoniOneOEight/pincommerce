import asyncio
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock

from tooling.integration.durable import SQLiteRuntimeStore
from tooling.integration.nats_client import close_nats, nats_connection
from tooling.integration.nats_transport import publish_event
from tooling.integration.production_runtime import ProductionIntegrationRuntime
from tooling.integration.runtime import DeliveryResult, DomainCommand, DomainEvent
from tooling.integration.webhooks import canonicalize_webhook


class FailingAdapter:
    provider = "failing"

    def __init__(self):
        self.calls = 0

    def execute(self, command):
        self.calls += 1
        return DeliveryResult(
            success=False,
            provider=self.provider,
            command_id=command.command_id,
            attempt=self.calls,
            error="downstream-unavailable",
        )


class SuccessAdapter:
    provider = "success"

    def __init__(self):
        self.calls = 0

    def execute(self, command):
        self.calls += 1
        return DeliveryResult(
            success=True,
            provider=self.provider,
            command_id=command.command_id,
            attempt=self.calls,
            external_id="EXT-1",
        )


class SlowSuccessAdapter(SuccessAdapter):
    def __init__(self, delay: float = 0.1):
        super().__init__()
        self.delay = delay

    def execute(self, command):
        time.sleep(self.delay)
        return super().execute(command)


class FakeNATS:
    def __init__(self):
        self.messages = []

    async def publish(self, subject, payload):
        self.messages.append((subject, payload))


class LifecycleNATS:
    def __init__(self):
        self.drained = 0
        self.closed = 0

    async def drain(self):
        self.drained += 1

    async def close(self):
        self.closed += 1


class IntegrationInfrastructureTests(unittest.TestCase):
    def test_durable_idempotency_survives_runtime_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "runtime.db"
            command = DomainCommand(
                command_id="cmd-1",
                command_type="erp.create_sales_order",
                target="erp",
                payload={},
                idempotency_key="durable-1",
            )

            with SQLiteRuntimeStore(db) as store1:
                runtime1 = ProductionIntegrationRuntime(store1)
                adapter1 = SuccessAdapter()
                runtime1.register("erp", adapter1)
                runtime1.dispatch(command)
                self.assertEqual(adapter1.calls, 1)

            with SQLiteRuntimeStore(db) as store2:
                runtime2 = ProductionIntegrationRuntime(store2)
                adapter2 = SuccessAdapter()
                runtime2.register("erp", adapter2)
                result = runtime2.dispatch(command)
                self.assertTrue(result.success)
                self.assertEqual(adapter2.calls, 0)

    def test_failed_command_moves_to_dead_letter(self):
        with tempfile.TemporaryDirectory() as tmp:
            with SQLiteRuntimeStore(Path(tmp) / "runtime.db") as store:
                runtime = ProductionIntegrationRuntime(store, sleep=lambda _: None)
                runtime.register("erp", FailingAdapter())
                command = DomainCommand(
                    command_id="cmd-fail",
                    command_type="erp.create_sales_order",
                    target="erp",
                    payload={},
                    idempotency_key="fail-1",
                    max_attempts=2,
                )
                result = runtime.dispatch(command)
                self.assertFalse(result.success)
                letters = runtime.delivery_exceptions()
                self.assertEqual(len(letters), 1)
                self.assertEqual(letters[0]["status"], "open")
                self.assertEqual(letters[0]["attempts"], 2)

    def test_sqlite_file_can_be_deleted_after_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "runtime.db"
            store = SQLiteRuntimeStore(db)
            store.append_audit({"event": "test"})
            store.close()
            store.close()  # idempotent
            db.unlink()
            self.assertFalse(db.exists())

    def test_concurrent_workers_execute_side_effect_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "runtime.db"
            command = DomainCommand(
                command_id="cmd-concurrent",
                command_type="erp.create_sales_order",
                target="erp",
                payload={},
                idempotency_key="concurrent-1",
            )
            barrier = threading.Barrier(2)
            results: list[DeliveryResult] = []
            calls: list[int] = []
            lock = threading.Lock()

            def worker():
                with SQLiteRuntimeStore(db) as store:
                    runtime = ProductionIntegrationRuntime(store, sleep=lambda _: None)
                    adapter = SlowSuccessAdapter()
                    runtime.register("erp", adapter)
                    barrier.wait()
                    result = runtime.dispatch(command)
                    with lock:
                        results.append(result)
                        calls.append(adapter.calls)

            threads = [threading.Thread(target=worker) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            self.assertEqual(sum(calls), 1)
            self.assertEqual(sum(1 for r in results if r.success), 1)
            self.assertEqual(sum(1 for r in results if r.pending), 1)

    def test_failed_key_is_reclaimable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with SQLiteRuntimeStore(Path(tmp) / "runtime.db") as store:
                first = store.claim("retry-key")
                self.assertTrue(first.acquired)
                self.assertEqual(store.claim("retry-key").state, "in_progress")

                store.fail(
                    "retry-key",
                    DeliveryResult(False, "erp", "cmd", 1, error="boom"),
                )
                second = store.claim("retry-key")
                self.assertTrue(second.acquired)

                store.complete(
                    "retry-key",
                    DeliveryResult(True, "erp", "cmd", 1, external_id="EXT"),
                )
                replay = store.claim("retry-key")
                self.assertFalse(replay.acquired)
                self.assertEqual(replay.state, "completed")
                assert replay.result is not None
                self.assertEqual(replay.result.external_id, "EXT")

    def test_claim_release_allows_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            with SQLiteRuntimeStore(Path(tmp) / "runtime.db") as store:
                self.assertTrue(store.claim("release-key").acquired)
                store.release("release-key")
                self.assertTrue(store.claim("release-key").acquired)

    def test_nats_close_drains_then_closes(self):
        connection = LifecycleNATS()
        asyncio.run(close_nats(connection))
        self.assertEqual(connection.drained, 1)
        self.assertEqual(connection.closed, 1)

    def test_nats_close_without_drain(self):
        connection = LifecycleNATS()
        asyncio.run(close_nats(connection, drain=False))
        self.assertEqual(connection.drained, 0)
        self.assertEqual(connection.closed, 1)

    def test_nats_close_accepts_none(self):
        asyncio.run(close_nats(None))

    def test_nats_connection_context_manager_drains_and_closes(self):
        connection = LifecycleNATS()

        async def fake_connect(url):
            self.assertEqual(url, "nats://example")
            return connection

        async def run():
            with mock.patch(
                "tooling.integration.nats_client.connect_nats", fake_connect
            ):
                async with nats_connection("nats://example") as conn:
                    self.assertIs(conn, connection)
                    self.assertEqual(connection.closed, 0)

        asyncio.run(run())
        self.assertEqual(connection.drained, 1)
        self.assertEqual(connection.closed, 1)

    def test_webhook_canonicalization(self):
        event = canonicalize_webhook(
            provider="medusa",
            webhook_type="order",
            payload={"id": "ORD-1", "total": 999},
        )
        self.assertEqual(event.event_type, "order.confirmed")
        self.assertEqual(event.aggregate_id, "ORD-1")

    def test_nats_subject_and_payload(self):
        event = DomainEvent(
            event_id="evt-1",
            event_type="order.confirmed",
            producer="commerce",
            aggregate_type="order",
            aggregate_id="ORD-1",
            payload={"total": 999},
            idempotency_key="evt-1",
        )
        client = FakeNATS()
        subject = asyncio.run(publish_event(client, event))
        self.assertEqual(subject, "pinaka.events.order.confirmed")
        self.assertEqual(len(client.messages), 1)


if __name__ == "__main__":
    unittest.main()
