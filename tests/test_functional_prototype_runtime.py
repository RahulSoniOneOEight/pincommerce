from pathlib import Path
import tempfile
import unittest

import yaml

from tooling.prototype.core_runtime import (
    CoreRuntimeError,
    assert_core_runtime_ready,
    build_core_runtime,
)
from tooling.prototype.demo_data import build_demo_dataset
from tooling.prototype.mock_providers import MockProviderRuntime


class FunctionalPrototypeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "client-projects/demo"
        for folder in ("input", "solution", "experience/fixtures", "experience"):
            (self.project / folder).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp.cleanup()

    def _write_client(self, models=None, overrides=None):
        (self.project / "input/client-input.yaml").write_text(
            yaml.safe_dump({
                "client_id": "demo",
                "industry": "retail",
                "business_models": models or ["d2c"],
                "source_refs": ["brief:demo"],
                "core_module_requirements": overrides or [],
                "required_integrations": ["payment", "logistics", "whatsapp"],
            }),
            encoding="utf-8",
        )

    def _write_solution(self, marketplace=False):
        providers = {
            "commerce": {"type": "commerce", "provider": "medusa"},
            "erp": {"type": "erp", "provider": "tryton"},
        }
        if marketplace:
            providers["marketplace"] = {"type": "marketplace", "provider": "mercur"}
        (self.project / "solution/solution-contract.yaml").write_text(
            yaml.safe_dump({"version": 1, "client": "demo", "providers": providers}),
            encoding="utf-8",
        )

    def test_standard_core_is_default_and_client_overrides_are_targeted(self):
        self._write_client(overrides=[{
            "requirement_id": "REQ-CORE-001",
            "module": "tryton",
            "target": "warehouse.transfer",
            "change": "require manager approval",
            "source_refs": ["brief:demo"],
        }])
        self._write_solution()
        runtime = build_core_runtime("demo", self.root)
        modules = {m["provider"]: m for m in runtime["modules"]}
        self.assertTrue(modules["medusa"]["required"])
        self.assertTrue(modules["tryton"]["required"])
        self.assertFalse(modules["mercur"]["required"])
        self.assertEqual(modules["medusa"]["overrides"], [])
        self.assertEqual(modules["tryton"]["overrides"][0]["target"], "warehouse.transfer")
        self.assertEqual(runtime["external_integrations"][0]["mode"], "mock")

    def test_marketplace_activates_mercur(self):
        self._write_client(models=["marketplace"])
        self._write_solution(marketplace=True)
        runtime = build_core_runtime("demo", self.root)
        modules = {m["provider"]: m for m in runtime["modules"]}
        self.assertTrue(modules["mercur"]["required"])
        self.assertEqual(modules["mercur"]["mode"], "real-core")

    def test_demo_dataset_has_linked_commerce_erp_finance_states(self):
        data = build_demo_dataset("demo")
        orders = {x["id"] for x in data["transactions"]["orders"]}
        invoice_orders = {x["order_id"] for x in data["finance"]["invoices"]}
        self.assertIn("ORD-1001", orders)
        self.assertIn("ORD-1001", invoice_orders)
        self.assertIn("reconciliation-mismatch", data["scenario_coverage"])
        for entry in data["finance"]["journal_entries"]:
            debit = sum(line["debit"] for line in entry["lines"])
            credit = sum(line["credit"] for line in entry["lines"])
            self.assertEqual(debit, credit)

    def test_external_provider_mocks_are_deterministic(self):
        runtime = MockProviderRuntime()
        payment = runtime.execute("razorpay", "payment-success", entity_id="ORD-1")
        shipment = runtime.execute("shiprocket", "shipment-created", entity_id="ORD-1")
        self.assertTrue(payment.success)
        self.assertEqual(payment.payload["external_id"], "pay_demo-ORD-1")
        self.assertEqual(shipment.payload["external_id"], "SRDEMO-ORD-1")

    def test_review_readiness_requires_real_core_health_evidence(self):
        self._write_client()
        self._write_solution()
        value = build_core_runtime("demo", self.root)
        (self.project / "experience/prototype-core-runtime.yaml").write_text(
            yaml.safe_dump(value), encoding="utf-8"
        )
        dataset = build_demo_dataset("demo")
        (self.project / "experience/fixtures/demo-demo-dataset.yaml").write_text(
            yaml.safe_dump(dataset), encoding="utf-8"
        )
        with self.assertRaises(CoreRuntimeError):
            assert_core_runtime_ready("demo", self.root)

        for module in value["modules"]:
            if module["required"]:
                module["status"] = "healthy"
                module["health"]["evidence_ref"] = f"runtime/health/{module['provider']}.json"
                module["seed_evidence_ref"] = f"runtime/seeds/{module['provider']}.json"
        value["status"] = "prototype-ready"
        (self.project / "experience/prototype-core-runtime.yaml").write_text(
            yaml.safe_dump(value), encoding="utf-8"
        )
        ready = assert_core_runtime_ready("demo", self.root)
        self.assertEqual(ready["status"], "prototype-ready")


if __name__ == "__main__":
    unittest.main()
