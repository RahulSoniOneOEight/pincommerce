from pathlib import Path
import tempfile
import unittest
import yaml

from tooling.contracts.validator import validate_document
from tooling.review.nowa_session import (
    NowaReviewError,
    add_edit,
    apply_minor_edit,
    client_confirm,
    create_live_session,
    record_qa,
    route_material_edit,
)
from tooling.review.freeze import FreezeError, build_scope_baseline


class NowaLiveReviewTests(unittest.TestCase):
    def test_minor_visual_edit_can_be_applied_live_then_qa_confirmed(self):
        session = create_live_session(
            "demo", "REV-DEMO", "BLD-DEMO", "agency-reviewer",
            ["agency-reviewer", "client-owner"]
        )
        session = add_edit(
            session,
            category="spacing",
            summary="Reduce card spacing",
            surface="customer-app",
            target="ProductCard.padding",
            before="24",
            after="20",
            git_paths=["packages/agency_flutter_ui/lib/product_card.dart"],
        )
        edit_id = session["edits"][0]["edit_id"]
        session = apply_minor_edit(
            session, edit_id, git_diff_ref="diff:123", resulting_revision="abc123"
        )
        self.assertEqual(session["status"], "qa-required")
        session = record_qa(session, ["experience/visual-qa/VQA-POST-NOWA.yaml"])
        self.assertEqual(session["status"], "qa-passed")
        session = client_confirm(session, "client-owner", "2026-09-22T10:30:00Z")
        self.assertEqual(session["status"], "client-confirmed")
        self.assertTrue(session["edits"][0]["client_confirmed"])
        self.assertEqual(validate_document(session, "live-review-session"), [])

    def test_material_change_cannot_be_applied_in_nowa(self):
        session = create_live_session(
            "demo", "REV-DEMO", "BLD-DEMO", "agency-reviewer", ["agency-reviewer"]
        )
        session = add_edit(
            session,
            category="business-rule",
            summary="Manager approval above threshold",
            surface="customer-app",
            target="checkout-approval",
        )
        edit_id = session["edits"][0]["edit_id"]
        self.assertEqual(session["edits"][0]["route"], "change-contract")
        with self.assertRaises(NowaReviewError):
            apply_minor_edit(
                session, edit_id, git_diff_ref="diff:bad", resulting_revision="bad123"
            )
        session = route_material_edit(session, edit_id, "changes/CHG-002.yaml")
        self.assertEqual(session["edits"][0]["status"], "change-contract-created")

    def test_client_confirmation_requires_post_change_qa(self):
        session = create_live_session(
            "demo", "REV-DEMO", "BLD-DEMO", "agency-reviewer", ["agency-reviewer"]
        )
        with self.assertRaises(NowaReviewError):
            client_confirm(session, "client-owner", "2026-09-22T10:30:00Z")

    def test_scope_freeze_blocks_unfinished_nowa_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "client-projects/demo"
            for folder in (
                "solution", "solution/decisions", "derived", "feedback",
                "experience/directions", "experience/visual-qa"
            ):
                (project / folder).mkdir(parents=True, exist_ok=True)

            (project / "solution/solution-contract.yaml").write_text(
                "version: 1\nclient: demo\nproviders: {}\n", encoding="utf-8"
            )
            (project / "derived/capability-map.yaml").write_text(
                "client_id: demo\nmandatory: [audit]\ncore: [checkout]\nrecommended: []\n"
                "requested_additional: []\nlater: []\nnot_applicable: []\n",
                encoding="utf-8",
            )
            (project / "experience/directions/a.yaml").write_text(
                "direction_id: DIR-DEMO-A\nclient_id: demo\nstrategy: discovery-first\n"
                "surfaces: [customer-app]\njourney_emphasis: [browse-to-buy]\n"
                "design_intent: {}\nstatus: draft\n",
                encoding="utf-8",
            )
            review = {
                "review_id": "REV-DEMO",
                "client_id": "demo",
                "build_id": "BLD-DEMO",
                "direction_id": "DIR-DEMO-A",
                "artifacts": [{
                    "artifact_id": "ART-1", "surface": "customer-app",
                    "environment": "prototype", "build_identity": "BLD-DEMO",
                    "approval_status": "approved"
                }],
                "status": "approved",
            }
            (project / "feedback/review.yaml").write_text(
                yaml.safe_dump(review), encoding="utf-8"
            )
            qa = {
                "qa_id": "VQA-DEMO", "client_id": "demo", "direction_id": "DIR-DEMO-A",
                "surface": "customer-app", "build_identity": "BLD-DEMO",
                "checks": [{"id": "visual", "status": "pass", "evidence": "capture", "notes": []}],
                "status": "passed",
            }
            (project / "experience/visual-qa/qa.yaml").write_text(
                yaml.safe_dump(qa), encoding="utf-8"
            )
            live = create_live_session(
                "demo", "REV-DEMO", "BLD-DEMO", "agency-reviewer", ["agency-reviewer"]
            )
            (project / "feedback/LIVE-demo-NOWA-001.yaml").write_text(
                yaml.safe_dump(live), encoding="utf-8"
            )

            with self.assertRaises(FreezeError):
                build_scope_baseline(
                    "demo",
                    review_file="review.yaml",
                    visual_qa_files=["qa.yaml"],
                    approved_by="client-owner",
                    approved_at="2026-09-22T11:00:00Z",
                    root=root,
                )


if __name__ == "__main__":
    unittest.main()
