from pathlib import Path
import tempfile
import unittest
import yaml

from tooling.review.bugdrop import triage, to_change_contract
from tooling.review.session import (
    create_build_identity,
    create_capture_manifest,
    create_review_session,
)


class ReviewToolingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        direction_dir = self.root / "client-projects/demo/experience/directions"
        direction_dir.mkdir(parents=True)
        (direction_dir / "a.yaml").write_text(
            "direction_id: DIR-DEMO-A\n"
            "client_id: demo\n"
            "strategy: discovery-first\n"
            "surfaces: [customer-app, web-store]\n"
            "journey_emphasis: [browse-to-buy]\n"
            "design_intent: {}\n"
            "status: draft\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_build_identity_is_immutable(self):
        build = create_build_identity(
            "demo", "a.yaml", "abcdef1234567890", "tester", root=self.root
        )
        self.assertTrue(build["immutable"])
        self.assertEqual(build["direction_id"], "DIR-DEMO-A")
        self.assertIn("abcdef123456", build["build_id"])

    def test_capture_plan_covers_flutter_and_web(self):
        build = create_build_identity(
            "demo", "a.yaml", "abcdef1234567890", "tester", root=self.root
        )
        capture = create_capture_manifest(
            build,
            {"customer-app": ["default", "failure"], "web-store": ["default", "failure"]},
        )
        runtimes = {item["runtime"] for item in capture["targets"]}
        self.assertIn("flutter", runtimes)
        self.assertIn("web", runtimes)
        self.assertTrue(any(item["viewport"] == "390x844" for item in capture["targets"]))

    def test_review_session_references_build(self):
        build = create_build_identity(
            "demo", "a.yaml", "abcdef1234567890", "tester", root=self.root
        )
        capture = create_capture_manifest(
            build,
            {"customer-app": ["default"], "web-store": ["default"]},
        )
        coverage = {
            "implementation_ref": "experience/prototypes/a-implementation.yaml",
            "surface_coverage": [
                {"surface": "customer-app", "required": True, "journeys": ["browse-to-buy"]},
                {"surface": "web-store", "required": True, "journeys": ["browse-to-buy"]},
            ],
        }
        review = create_review_session(build, capture, coverage, None)
        self.assertEqual(review["build_id"], build["build_id"])
        self.assertTrue(review["artifacts"])
        self.assertEqual(
            {item["surface"] for item in review["surface_approvals"]},
            {"customer-app", "web-store"},
        )
        self.assertEqual(review["journey_approvals"][0]["journey"], "browse-to-buy")

    def test_material_bugdrop_becomes_change_contract(self):
        bug = {
            "bugdrop_id": "BUG-DEMO-001",
            "client_id": "demo",
            "review_id": "REV-DEMO",
            "artifact_id": "ART-0001",
            "category": "business-rule",
            "summary": "Approval required above threshold",
            "severity": "high",
            "affected_capabilities": ["checkout"],
            "affected_domains": ["commerce"],
            "affected_surfaces": ["web-store"],
            "status": "open",
        }
        triaged = triage(bug)
        self.assertTrue(triaged["triage"]["requires_change_contract"])
        change = to_change_contract(bug, "CHG-001")
        self.assertEqual(change["type"], "business-rule")
        self.assertTrue(change["approval_required"])


if __name__ == "__main__":
    unittest.main()
