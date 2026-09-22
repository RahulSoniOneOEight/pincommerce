from pathlib import Path
import tempfile
import unittest
import yaml

from tooling.review.review_round import (
    ReviewRoundError,
    add_feedback,
    approve_target,
    classify_feedback,
    create_prototype_revision,
    create_review_round,
    finalize_round,
    record_qa,
    resolve_feedback,
    route_feedback,
)


class PrototypeRevisionReviewRoundTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "client-projects/demo"
        for folder in (
            "feedback", "feedback/rounds", "feedback/items",
            "experience/builds", "experience/revisions", "experience/prototypes",
        ):
            (self.project / folder).mkdir(parents=True, exist_ok=True)

        review = {
            "review_id": "REV-BLD-demo-a-abc123",
            "client_id": "demo",
            "build_id": "BLD-demo-a-abc123",
            "direction_id": "DIR-DEMO-A",
            "coverage_ref": "experience/prototypes/a-coverage.yaml",
            "implementation_ref": "experience/prototypes/a-implementation.yaml",
            "core_runtime_ref": None,
            "demo_dataset_ref": None,
            "surface_approvals": [
                {"surface": "customer-app", "status": "pending"},
                {"surface": "web-store", "status": "pending"},
            ],
            "journey_approvals": [
                {"journey": "browse-to-buy", "status": "pending"},
                {"journey": "credit-order", "status": "pending"},
            ],
            "artifacts": [],
            "status": "draft",
        }
        (self.project / "feedback/review.yaml").write_text(
            yaml.safe_dump(review), encoding="utf-8"
        )
        (self.project / "experience/builds/BLD-demo-a-abc123.yaml").write_text(
            yaml.safe_dump({
                "build_id": "BLD-demo-a-abc123",
                "client_id": "demo",
                "direction_id": "DIR-DEMO-A",
                "source_revision": "abc123456789",
                "environment": "prototype",
                "surfaces": ["customer-app", "web-store"],
                "created_by": "tester",
                "immutable": True,
            }),
            encoding="utf-8",
        )
        (self.project / "experience/prototypes/a-coverage.yaml").write_text(
            yaml.safe_dump({
                "coverage_id": "COV-demo-a",
                "client_id": "demo",
                "direction_id": "DIR-DEMO-A",
                "prototype_manifest_ref": "experience/prototypes/a-manifest.yaml",
                "implementation_ref": "experience/prototypes/a-implementation.yaml",
                "requirements": [],
                "surface_coverage": [
                    {
                        "surface": "customer-app",
                        "required": True,
                        "screens": ["home"],
                        "components": ["navigation"],
                        "states": ["default"],
                        "journeys": ["browse-to-buy", "credit-order"],
                        "status": "complete",
                    },
                    {
                        "surface": "web-store",
                        "required": True,
                        "screens": ["home"],
                        "components": ["navigation"],
                        "states": ["default"],
                        "journeys": ["browse-to-buy", "credit-order"],
                        "status": "complete",
                    },
                ],
                "blocking_items": [],
                "status": "client-review-ready",
            }),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_text_feedback_is_classified_and_routed(self):
        self.assertEqual(
            classify_feedback("visual", "request-change"),
            ("minor-change", "nowa"),
        )
        self.assertEqual(
            classify_feedback("business-rule", "request-change"),
            ("material-change", "change-contract"),
        )
        self.assertEqual(
            classify_feedback("visual", "approve"),
            ("approval", "none"),
        )

    def test_revision_round_feedback_and_final_approval_loop(self):
        revision = create_prototype_revision(
            "demo",
            review_file="review.yaml",
            sequence=1,
            created_by="tester",
            root=self.root,
        )
        self.assertEqual(revision["revision_id"], "PROTO-demo-a-001")
        self.assertTrue(revision["immutable"])

        revision_path = self.project / "experience/revisions/PROTO-demo-a-001.yaml"
        revision_path.write_text(yaml.safe_dump(revision), encoding="utf-8")

        round_value = create_review_round(
            "demo",
            revision_file=revision_path.name,
            review_file="review.yaml",
            sequence=1,
            root=self.root,
        )
        self.assertEqual(round_value["round_id"], "ROUND-demo-a-001")

        round_value, feedback = add_feedback(
            round_value,
            surface="customer-app",
            journey="credit-order",
            screen="checkout",
            component="credit-limit-card",
            feedback_type="visual",
            comment="Move available credit above the payment options.",
            action="request-change",
            created_by="client-owner",
        )
        self.assertEqual(feedback["classification"], "minor-change")
        self.assertEqual(feedback["route"], "nowa")
        self.assertEqual(round_value["outcome"], "changes-requested")

        round_value, feedback = route_feedback(
            round_value,
            feedback,
            live_review_ref="feedback/LIVE-DEMO-001.yaml",
        )
        self.assertEqual(feedback["status"], "routed")
        feedback = resolve_feedback(feedback)

        round_value = approve_target(round_value, surface="customer-app")
        round_value = approve_target(round_value, surface="web-store")
        round_value = approve_target(round_value, journey="browse-to-buy")
        round_value = approve_target(round_value, journey="credit-order")
        round_value = record_qa(
            round_value,
            ["experience/visual-qa/VQA-BLD-demo-a-abc123-customer-app.yaml"],
        )
        final = finalize_round(round_value, [feedback])
        self.assertEqual(final["outcome"], "approved")

    def test_material_feedback_requires_change_contract_route(self):
        revision = create_prototype_revision(
            "demo", review_file="review.yaml", sequence=1,
            created_by="tester", root=self.root,
        )
        (self.project / "experience/revisions/PROTO-demo-a-001.yaml").write_text(
            yaml.safe_dump(revision), encoding="utf-8"
        )
        round_value = create_review_round(
            "demo",
            revision_file="PROTO-demo-a-001.yaml",
            review_file="review.yaml",
            sequence=1,
            root=self.root,
        )
        round_value, feedback = add_feedback(
            round_value,
            surface="web-store",
            journey="credit-order",
            feedback_type="business-rule",
            comment="Orders above two lakh require manager approval.",
            action="request-change",
        )
        with self.assertRaises(ReviewRoundError):
            route_feedback(round_value, feedback, live_review_ref="feedback/LIVE.yaml")
        round_value, feedback = route_feedback(
            round_value,
            feedback,
            change_contract_ref="changes/CHG-201.yaml",
        )
        self.assertIn("changes/CHG-201.yaml", round_value["change_refs"])


if __name__ == "__main__":
    unittest.main()
