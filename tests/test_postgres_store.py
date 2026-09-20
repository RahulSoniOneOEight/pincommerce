import unittest

from tooling.integration.postgres_store import PostgresRuntimeStore
from tooling.integration.runtime import DeliveryResult


class FakeCursor:
    """Minimal DB-API cursor that emulates the store's SQL semantics.

    The point is not to reimplement PostgreSQL, but to exercise the store's
    claim/lifecycle logic and to assert that the production store relies on
    atomic, set-based statements (``on conflict ... do nothing`` and the
    conditional ``where state = 'failed'`` update) rather than in-process locks.
    """

    def __init__(self, conn):
        self.conn = conn
        self.rowcount = 0
        self._rows: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, sql, params=()):
        statement = " ".join(sql.split())
        self.conn.sql_log.append(statement)
        self.rowcount = 0
        self._rows = []

        if statement.startswith("create table") or statement.startswith("alter table"):
            return

        if statement.startswith("select result_json from integration_idempotency"):
            row = self.conn.idempotency.get(params[0])
            self._rows = [(row["result_json"],)] if row else []
            return

        if statement.startswith("insert into integration_idempotency"):
            if "do nothing" in statement:
                key = params[0]
                if key in self.conn.idempotency:
                    return
                self.conn.idempotency[key] = {
                    "state": "processing",
                    "result_json": None,
                }
                self.rowcount = 1
            else:
                key, payload = params
                self.conn.idempotency[key] = {
                    "state": "completed",
                    "result_json": payload,
                }
                self.rowcount = 1
            return

        if statement.startswith("select state, result_json from integration_idempotency"):
            row = self.conn.idempotency.get(params[0])
            self._rows = [(row["state"], row["result_json"])] if row else []
            return

        if statement.startswith("update integration_idempotency"):
            if "and state = 'failed'" in statement:
                row = self.conn.idempotency.get(params[0])
                if row and row["state"] == "failed":
                    row["state"] = "processing"
                    self.rowcount = 1
                return
            state, payload, key = params
            row = self.conn.idempotency.get(key)
            if row:
                row["state"] = state
                row["result_json"] = payload
                self.rowcount = 1
            return

        if statement.startswith("delete from integration_idempotency"):
            row = self.conn.idempotency.get(params[0])
            if row and row["state"] == "processing":
                del self.conn.idempotency[params[0]]
                self.rowcount = 1
            return

        if statement.startswith("insert into integration_audit"):
            self.conn.audit.append(params[0])
            return

        if statement.startswith("insert into integration_dead_letter"):
            dead_letter_id, payload = params
            self.conn.dead_letters[dead_letter_id] = payload
            self.rowcount = 1
            return

        if statement.startswith(
            "select payload_json from integration_dead_letter where"
        ):
            value = self.conn.dead_letters.get(params[0])
            self._rows = [(value,)] if value is not None else []
            return

        if statement.startswith(
            "select payload_json from integration_dead_letter order"
        ):
            self._rows = [
                (value,) for _, value in sorted(self.conn.dead_letters.items())
            ]
            return

        raise AssertionError(f"Unexpected SQL: {statement}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConnection:
    def __init__(self):
        self.idempotency: dict[str, dict] = {}
        self.dead_letters: dict[str, str] = {}
        self.audit: list[str] = []
        self.sql_log: list[str] = []
        self.commits = 0
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def result(success: bool = True, external_id: str | None = "EXT-1") -> DeliveryResult:
    return DeliveryResult(
        success=success,
        provider="erp",
        command_id="cmd-1",
        attempt=1,
        external_id=external_id,
        error=None if success else "boom",
    )


class PostgresStoreTests(unittest.TestCase):
    def setUp(self):
        self.connection = FakeConnection()
        self.store = PostgresRuntimeStore(self.connection)

    def test_claim_lifecycle(self):
        first = self.store.claim("key-1")
        self.assertTrue(first.acquired)
        self.assertEqual(first.state, "acquired")

        second = self.store.claim("key-1")
        self.assertFalse(second.acquired)
        self.assertEqual(second.state, "in_progress")

        self.store.fail("key-1", result(success=False))
        reacquired = self.store.claim("key-1")
        self.assertTrue(reacquired.acquired)

        self.store.complete("key-1", result(external_id="EXT-9"))
        replay = self.store.claim("key-1")
        self.assertFalse(replay.acquired)
        self.assertEqual(replay.state, "completed")
        assert replay.result is not None
        self.assertEqual(replay.result.external_id, "EXT-9")

    def test_put_result_roundtrip(self):
        self.store.put_result("key-2", result(external_id="EXT-2"))
        fetched = self.store.get_result("key-2")
        assert fetched is not None
        self.assertEqual(fetched.external_id, "EXT-2")

    def test_claim_uses_atomic_conflict_statement(self):
        self.store.claim("key-3")
        self.assertTrue(
            any("on conflict(key) do nothing" in sql for sql in self.connection.sql_log)
        )

    def test_reacquire_targets_failed_state_only(self):
        self.store.claim("key-4")
        self.store.fail("key-4", result(success=False))
        self.store.claim("key-4")
        self.assertTrue(
            any(
                "and state = 'failed'" in sql for sql in self.connection.sql_log
            )
        )

    def test_release_only_removes_processing(self):
        self.store.claim("key-5")
        self.store.release("key-5")
        self.assertIsNone(self.connection.idempotency.get("key-5"))

        self.store.claim("key-6")
        self.store.complete("key-6", result())
        self.store.release("key-6")
        self.assertIn("key-6", self.connection.idempotency)

    def test_dead_letter_roundtrip(self):
        self.store.put_dead_letter({"dead_letter_id": "DLQ-1", "status": "open"})
        self.store.put_dead_letter({"dead_letter_id": "DLQ-2", "status": "open"})
        fetched = self.store.get_dead_letter("DLQ-1")
        assert fetched is not None
        self.assertEqual(fetched["dead_letter_id"], "DLQ-1")
        self.assertEqual(
            [item["dead_letter_id"] for item in self.store.list_dead_letters()],
            ["DLQ-1", "DLQ-2"],
        )

    def test_close_is_idempotent(self):
        self.store.close()
        self.store.close()
        self.assertTrue(self.connection.closed)

    def test_context_manager_closes(self):
        with PostgresRuntimeStore(FakeConnection()) as store:
            self.assertFalse(store.conn.closed)
        self.assertTrue(store.conn.closed)


if __name__ == "__main__":
    unittest.main()
