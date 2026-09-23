from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from tooling.onboarding.engine import (
    classify_archetypes,
    infer_dependency_map,
    infer_entity_map,
    load_archetype,
    resolve_benchmark,
    resolve_solution_contract,
)
from tooling.production.compiler import (
    CAPABILITY_OWNERS,
    PROVIDER_ADAPTERS,
    SURFACE_PROVIDER_KEYS,
    build_migration_steps,
)
from tooling.prototype.core_runtime import build_core_runtime
from tooling.prototype.demo_data import build_demo_dataset
from tooling.prototype.seed_bundle import build_seed_bundle

ROOT = Path(__file__).resolve().parents[1]


class MarketplaceAToDTests(unittest.TestCase):
    def test_a_marketplace_business_models_activate_marketplace_archetype(self):
        for model in ("marketplace", "b2b-marketplace", "multi-vendor"):
            self.assertIn("marketplace", classify_archetypes([model]))

        archetype = load_archetype(ROOT, "marketplace")
        benchmark = resolve_benchmark(
            {
                "client_id": "market-demo",
                "industry": "retail",
                "business_models": ["marketplace"],
            },
            {"core_capabilities": [], "recommended_capabilities": [], "controls": [], "qa_emphasis": []},
            [archetype],
        )
        expected = benchmark["expected"]
        self.assertIn("seller-portal", expected["surfaces"])
        self.assertIn("seller-onboarding", expected["core_capabilities"])
        self.assertIn("commissions", expected["core_capabilities"])
        self.assertIn("settlements", expected["core_capabilities"])
        self.assertIn("seller-settlement", expected["journeys"])

    def test_b_marketplace_entities_flows_and_solution_select_mercur(self):
        capabilities = [
            "catalogue",
            "orders",
            "seller-onboarding",
            "seller-catalogue",
            "seller-inventory",
            "marketplace-orders",
            "commissions",
            "settlements",
            "payout-reconciliation",
        ]
        entities = infer_entity_map("market-demo", capabilities)["entities"]
        for entity in (
            "seller",
            "seller-offer",
            "marketplace-order-allocation",
            "commission",
            "seller-settlement",
            "seller-payout-reconciliation",
        ):
            self.assertIn(entity, entities)

        flows = {
            item["id"]
            for item in infer_dependency_map("market-demo", capabilities)["critical_cross_domain_flows"]
        }
        self.assertIn("seller-onboarding-to-approval", flows)
        self.assertIn("commerce-order-to-seller-allocation", flows)
        self.assertIn("seller-settlement-to-accounting", flows)

        solution = resolve_solution_contract(
            "market-demo",
            capabilities,
            ["web-store", "commerce-admin", "seller-portal", "erp"],
            ROOT,
        )
        self.assertEqual(solution["providers"]["marketplace"]["provider"], "mercur")
        self.assertEqual(solution["providers"]["commerce"]["provider"], "medusa")
        self.assertEqual(solution["providers"]["erp"]["provider"], "tryton")

    def test_c_marketplace_requires_real_mercur_and_seed_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "client-projects" / "market-demo"
            (project / "input").mkdir(parents=True)
            (project / "solution").mkdir(parents=True)
            (project / "input/client-input.yaml").write_text(
                yaml.safe_dump(
                    {
                        "client_id": "market-demo",
                        "industry": "retail",
                        "business_models": ["multi-vendor"],
                        "required_integrations": ["payment", "logistics", "whatsapp"],
                        "marketplace_requirements": {
                            "commission_model": "percentage",
                            "settlement_cycle": "weekly",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (project / "solution/solution-contract.yaml").write_text(
                yaml.safe_dump(
                    {
                        "version": 1,
                        "client": "market-demo",
                        "providers": {
                            "commerce": {"type": "commerce", "provider": "medusa"},
                            "marketplace": {"type": "marketplace", "provider": "mercur"},
                            "erp": {"type": "erp", "provider": "tryton"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            runtime = build_core_runtime("market-demo", root)
            modules = {item["provider"]: item for item in runtime["modules"]}
            self.assertTrue(modules["mercur"]["required"])
            self.assertEqual(modules["mercur"]["mode"], "real-core")

        dataset = build_demo_dataset("market-demo")
        bundle = build_seed_bundle(dataset)["mercur"]
        self.assertGreaterEqual(len(bundle["sellers"]), 2)
        self.assertTrue(bundle["seller_offers"])
        self.assertTrue(bundle["marketplace_allocations"])
        self.assertTrue(bundle["commission_ledger"])
        self.assertTrue(bundle["seller_settlements"])
        self.assertTrue(bundle["seller_payout_reconciliations"])

    def test_d_marketplace_capabilities_surfaces_and_migration_are_owned(self):
        for capability in (
            "seller-onboarding",
            "seller-catalogue",
            "seller-inventory",
            "marketplace-orders",
            "commissions",
            "settlements",
            "seller-analytics",
            "seller-approval",
            "payout-reconciliation",
        ):
            self.assertEqual(CAPABILITY_OWNERS[capability], "marketplace")

        self.assertEqual(SURFACE_PROVIDER_KEYS["seller-portal"], "marketplace")
        self.assertEqual(
            PROVIDER_ADAPTERS["mercur"],
            "platform/marketplace/mercur/adapter.yaml",
        )

        steps = {item["id"]: item for item in build_migration_steps(True)}
        self.assertIn("migrate-marketplace-sellers", steps)
        self.assertIn("load-opening-seller-settlements", steps)
        self.assertEqual(steps["migrate-marketplace-sellers"]["target"], "marketplace")
        self.assertEqual(
            steps["load-opening-seller-settlements"]["target"],
            "marketplace-and-erp",
        )

        retail_steps = {item["id"] for item in build_migration_steps(False)}
        self.assertNotIn("migrate-marketplace-sellers", retail_steps)


if __name__ == "__main__":
    unittest.main()
