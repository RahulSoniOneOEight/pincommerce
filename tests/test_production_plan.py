from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from tooling.contracts.validator import validate_document
from tooling.production.compiler import (
    PROVIDER_ADAPTERS,
    build_production_plan,
    write_production_plan,
)
from tooling.production.readiness import evaluate_readiness, write_readiness

ROOT = Path(__file__).resolve().parents[1]


class ProductionPlanCompilerTests(unittest.TestCase):
    def test_reference_plan_exposes_real_d1_blockers(self):
        plan, _, _, _, migration = build_production_plan("reference-retail", ROOT)

        self.assertEqual(plan["scope"]["current_scope_ref"], "approved/current-scope.yaml")
        self.assertEqual(plan["scope"]["baseline_id"], "BASE-reference-retail-v1")
        self.assertEqual(plan["configuration"]["strategy"], "standard-baseline-plus-approved-overlays")
        self.assertEqual(validate_document(plan, "production-plan"), [])
        self.assertEqual(validate_document(migration, "production-migration-plan"), [])

        blockers = "\n".join(plan["blocking_items"])
        self.assertIn("payment", blockers)
        self.assertIn("logistics", blockers)
        self.assertNotIn("whatsapp", blockers)

        included = {item["id"] for item in plan["capabilities"]}
        self.assertIn("checkout", included)
        self.assertIn("credit-management", included)

    def test_reference_can_become_production_ready_only_after_explicit_d1_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = ROOT / "client-projects" / "reference-retail"
            dst = root / "client-projects" / "reference-retail"
            shutil.copytree(src, dst)

            # Provider adapter existence remains part of compiler validation.
            for adapter in {
                value for value in PROVIDER_ADAPTERS.values()
                if value.startswith("platform/")
            }:
                target = root / adapter
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("reference: true\n", encoding="utf-8")

            # Explicit D1 provider selections resolve ambiguous approved candidates.
            selections = {
                "integrations": {
                    "payment": "razorpay",
                    "logistics": "shiprocket",
                    "whatsapp": "meta-whatsapp-cloud",
                },
                "runtime_versions": {
                    "experience_mobile": "acceptance-flutter-pin",
                    "experience_web": "acceptance-nextjs-pin",
                    "commerce": "acceptance-medusa-pin",
                    "erp": "acceptance-tryton-pin",
                    "search": "acceptance-meilisearch-pin",
                    "support": "acceptance-chatwoot-pin",
                    "automation": "acceptance-activepieces-pin",
                    "database": "acceptance-postgresql-pin",
                },
            }
            selection_path = dst / "production" / "provider-selections.yaml"
            selection_path.parent.mkdir(parents=True, exist_ok=True)
            selection_path.write_text(
                yaml.safe_dump(selections, sort_keys=False), encoding="utf-8"
            )

            # Production version pins are D1 operational inputs. The approved
            # Solution Contract remains unchanged.
            outputs = write_production_plan("reference-retail", root)
            self.assertEqual(len(outputs), 6)
            readiness = evaluate_readiness("reference-retail", root)
            self.assertEqual(readiness["blocking_items"], [])
            self.assertEqual(readiness["status"], "production-ready")
            self.assertEqual(validate_document(readiness, "production-readiness"), [])

            readiness_path = write_readiness("reference-retail", root)
            self.assertTrue(readiness_path.exists())

            plan = yaml.safe_load(
                (dst / "production" / "production-plan.yaml").read_text(encoding="utf-8")
            )
            integration = {
                item["integration_id"]: item for item in plan["integrations"]
            }
            self.assertEqual(integration["payment"]["selected_provider"], "razorpay")
            self.assertEqual(integration["logistics"]["selected_provider"], "shiprocket")
            self.assertEqual(integration["whatsapp"]["selected_provider"], "meta-whatsapp-cloud")

    def test_readiness_blocks_unpinned_runtime_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = ROOT / "client-projects" / "reference-retail"
            dst = root / "client-projects" / "reference-retail"
            shutil.copytree(src, dst)
            for adapter in {
                value for value in PROVIDER_ADAPTERS.values()
                if value.startswith("platform/")
            }:
                target = root / adapter
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("reference: true\n", encoding="utf-8")
            (dst / "production" / "provider-selections.yaml").write_text(
                yaml.safe_dump({
                    "integrations": {
                        "payment": "razorpay",
                        "logistics": "shiprocket",
                        "whatsapp": "meta-whatsapp-cloud",
                    },
                    "runtime_versions": {},
                }),
                encoding="utf-8",
            )
            write_production_plan("reference-retail", root)
            readiness = evaluate_readiness("reference-retail", root)
            check = next(
                item for item in readiness["checks"]
                if item["id"] == "runtime-version-pinning"
            )
            self.assertEqual(check["status"], "fail")
            self.assertEqual(readiness["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
