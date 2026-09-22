from pathlib import Path
import tempfile
import unittest
import yaml

from tooling.experience.coverage import CoverageError, assert_client_review_ready, build_coverage


class PrototypeCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "client-projects/demo"
        for folder in [
            "input",
            "derived",
            "experience/directions",
            "experience/prototypes",
        ]:
            (self.project / folder).mkdir(parents=True, exist_ok=True)

        (self.project / "derived/capability-map.yaml").write_text(
            yaml.safe_dump({
                "client_id": "demo",
                "mandatory": ["authentication"],
                "core": ["catalogue", "checkout"],
                "recommended": [],
                "requested_additional": [],
            }),
            encoding="utf-8",
        )
        (self.project / "derived/journey-map.yaml").write_text(
            yaml.safe_dump({
                "client_id": "demo",
                "journeys": [{"id": "browse-to-buy", "status": "required"}],
            }),
            encoding="utf-8",
        )
        (self.project / "derived/surface-map.yaml").write_text(
            yaml.safe_dump({"client_id": "demo", "required": ["customer-app"], "recommended": []}),
            encoding="utf-8",
        )
        (self.project / "experience/directions/a.yaml").write_text(
            yaml.safe_dump({
                "direction_id": "DIR-DEMO-A",
                "client_id": "demo",
                "strategy": "discovery-first",
                "surfaces": ["customer-app"],
                "journey_emphasis": ["browse-to-buy"],
                "design_intent": {},
                "status": "draft",
            }),
            encoding="utf-8",
        )
        (self.project / "experience/prototypes/a-manifest.yaml").write_text(
            yaml.safe_dump({
                "client_id": "demo",
                "direction_id": "DIR-DEMO-A",
                "build_identity": "unbuilt",
                "requirements_source": "input/client-input.yaml#experience_requirements",
                "coverage_ref": "experience/prototypes/a-coverage.yaml",
                "surfaces": [{"id": "customer-app", "runtime": "flutter", "entry": "apps/prototype_app"}],
                "fixtures": ["commerce-baseline"],
                "status": "draft",
            }),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def _write_input(self, requirements):
        (self.project / "input/client-input.yaml").write_text(
            yaml.safe_dump({
                "client_id": "demo",
                "industry": "retail",
                "business_models": ["d2c"],
                "source_refs": ["brief:demo"],
                "experience_requirements": requirements,
            }),
            encoding="utf-8",
        )

    def test_unmapped_client_brief_requirement_blocks_review(self):
        self._write_input(["Dealer can upload a purchase-order PDF during checkout"])
        coverage = build_coverage("demo", "a.yaml", self.root, require_implementation=False)
        self.assertEqual(coverage["requirements"][0]["status"], "unmapped")
        self.assertEqual(coverage["status"], "incomplete")
        self.assertTrue(any("REQ-CLIENT-001" in item for item in coverage["blocking_items"]))

    def test_complete_ui_evidence_makes_prototype_review_ready(self):
        self._write_input([{
            "requirement_id": "REQ-DEMO-001",
            "statement": "Show available credit at checkout",
            "ux_impact": True,
            "requested_surfaces": ["customer-app"],
            "requested_screens": ["checkout"],
            "requested_components": ["credit-limit-card"],
            "required_states": ["available", "limit-exceeded"],
            "source_refs": ["brief:demo"],
        }])
        planned = build_coverage("demo", "a.yaml", self.root, require_implementation=False)
        surface = planned["surface_coverage"][0]
        implementation = {
            "implementation_id": "IMP-demo-a",
            "client_id": "demo",
            "direction_id": "DIR-DEMO-A",
            "surfaces": [{
                "surface": "customer-app",
                "runtime_ref": "apps/prototype_app",
                "screens": [
                    {"id": item, "status": "implemented", "evidence_ref": f"apps/prototype_app#{item}"}
                    for item in surface["screens"]
                ],
                "components": [
                    {"id": item, "status": "implemented", "evidence_ref": f"packages/agency_flutter_ui#{item}"}
                    for item in surface["components"]
                ],
                "states": [
                    {"id": item, "status": "implemented", "evidence_ref": f"fixtures#{item}"}
                    for item in surface["states"]
                ],
                "status": "complete",
            }],
            "status": "complete",
        }
        (self.project / "experience/prototypes/a-implementation.yaml").write_text(
            yaml.safe_dump(implementation), encoding="utf-8"
        )
        coverage = assert_client_review_ready("demo", "a.yaml", self.root)
        self.assertEqual(coverage["status"], "client-review-ready")
        self.assertEqual(coverage["requirements"][0]["status"], "covered")
        self.assertEqual(
            coverage["implementation_ref"],
            "experience/prototypes/a-implementation.yaml",
        )

    def test_missing_implementation_evidence_blocks_even_when_requirement_is_mapped(self):
        self._write_input([{
            "requirement_id": "REQ-DEMO-002",
            "statement": "Show coupon entry in cart",
            "ux_impact": True,
            "requested_surfaces": ["customer-app"],
            "requested_screens": ["cart"],
            "requested_components": ["coupon-entry"],
            "required_states": ["coupon-valid", "coupon-invalid"],
        }])
        with self.assertRaises(CoverageError):
            assert_client_review_ready("demo", "a.yaml", self.root)

    def test_capability_ui_is_scoped_to_relevant_surfaces(self):
        self._write_input([])
        (self.project / "derived/surface-map.yaml").write_text(
            yaml.safe_dump({
                "client_id": "demo",
                "required": ["customer-app", "erp"],
                "recommended": [],
            }),
            encoding="utf-8",
        )
        direction = yaml.safe_load(
            (self.project / "experience/directions/a.yaml").read_text(encoding="utf-8")
        )
        direction["surfaces"] = ["customer-app", "erp"]
        (self.project / "experience/directions/a.yaml").write_text(
            yaml.safe_dump(direction), encoding="utf-8"
        )
        manifest = yaml.safe_load(
            (self.project / "experience/prototypes/a-manifest.yaml").read_text(encoding="utf-8")
        )
        manifest["surfaces"].append({
            "id": "erp",
            "runtime": "external",
            "entry": "external/erp",
        })
        (self.project / "experience/prototypes/a-manifest.yaml").write_text(
            yaml.safe_dump(manifest), encoding="utf-8"
        )
        coverage = build_coverage(
            "demo", "a.yaml", self.root, require_implementation=False
        )
        by_surface = {
            item["surface"]: item for item in coverage["surface_coverage"]
        }
        self.assertIn("checkout", by_surface["customer-app"]["screens"])
        self.assertNotIn("checkout", by_surface["erp"]["screens"])
        self.assertIn("sales-orders", by_surface["erp"]["screens"])


if __name__ == "__main__":
    unittest.main()
