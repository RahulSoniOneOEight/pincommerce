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
from tooling.review.visual_qa import REQUIRED_CHECKS
from tooling.experience.coverage import build_coverage


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
                "input", "solution", "solution/decisions", "derived", "feedback",
                "experience/directions", "experience/prototypes", "experience/revisions",
                "experience/visual-qa", "feedback/rounds", "feedback/items"
            ):
                (project / folder).mkdir(parents=True, exist_ok=True)

            (project / "input/client-input.yaml").write_text(
                yaml.safe_dump({
                    "client_id": "demo",
                    "industry": "retail",
                    "business_models": ["d2c"],
                    "experience_requirements": [],
                }),
                encoding="utf-8",
            )
            (project / "derived/truth-register.yaml").write_text(
                yaml.safe_dump({
                    "client_id": "demo",
                    "version": 1,
                    "records": [{
                        "truth_id": "TRUTH-0001",
                        "path": "industry",
                        "value": "retail",
                        "classification": "fact",
                        "confidence": 1.0,
                        "sources": ["input/client-input.yaml"],
                        "status": "confirmed",
                        "notes": [],
                    }],
                    "open_questions": [],
                    "conflicts": [],
                    "status": "review-ready",
                }),
                encoding="utf-8",
            )
            (project / "solution/solution-contract.yaml").write_text(
                "version: 1\nclient: demo\nproviders: {}\n", encoding="utf-8"
            )
            (project / "derived/capability-map.yaml").write_text(
                "client_id: demo\nmandatory: []\ncore: []\nrecommended: []\n"
                "requested_additional: []\nlater: []\nnot_applicable: []\n",
                encoding="utf-8",
            )
            (project / "derived/surface-map.yaml").write_text(
                "client_id: demo\nrequired: [customer-app]\nrecommended: []\n",
                encoding="utf-8",
            )
            (project / "derived/journey-map.yaml").write_text(
                "client_id: demo\njourneys:\n  - {id: browse-to-buy, status: required}\n",
                encoding="utf-8",
            )
            (project / "experience/directions/a.yaml").write_text(
                "direction_id: DIR-DEMO-A\nclient_id: demo\nstrategy: discovery-first\n"
                "surfaces: [customer-app]\njourney_emphasis: [browse-to-buy]\n"
                "design_intent: {}\nstatus: draft\n",
                encoding="utf-8",
            )
            (project / "experience/prototypes/a-manifest.yaml").write_text(
                yaml.safe_dump({
                    "client_id": "demo",
                    "direction_id": "DIR-DEMO-A",
                    "build_identity": "unbuilt",
                    "requirements_source": "input/client-input.yaml#experience_requirements",
                    "coverage_ref": "experience/prototypes/a-coverage.yaml",
                    "surfaces": [{
                        "id": "customer-app",
                        "runtime": "flutter",
                        "entry": "apps/prototype_app",
                    }],
                    "fixtures": ["commerce-baseline"],
                    "status": "draft",
                }),
                encoding="utf-8",
            )
            planned = build_coverage("demo", "a.yaml", root, require_implementation=False)
            surface = planned["surface_coverage"][0]
            (project / "experience/prototypes/a-implementation.yaml").write_text(
                yaml.safe_dump({
                    "implementation_id": "IMP-demo-a",
                    "client_id": "demo",
                    "direction_id": "DIR-DEMO-A",
                    "surfaces": [{
                        "surface": "customer-app",
                        "runtime_ref": "apps/prototype_app",
                        "screens": [
                            {"id": x, "status": "implemented", "evidence_ref": f"app#{x}"}
                            for x in surface["screens"]
                        ],
                        "components": [
                            {"id": x, "status": "implemented", "evidence_ref": f"ui#{x}"}
                            for x in surface["components"]
                        ],
                        "states": [
                            {"id": x, "status": "implemented", "evidence_ref": f"fixture#{x}"}
                            for x in surface["states"]
                        ],
                        "status": "complete",
                    }],
                    "status": "complete",
                }),
                encoding="utf-8",
            )

            live = create_live_session(
                "demo", "REV-DEMO", "BLD-DEMO", "agency-reviewer", ["agency-reviewer"]
            )
            live_path = project / "feedback/LIVE-demo-NOWA-001.yaml"
            live_path.write_text(yaml.safe_dump(live), encoding="utf-8")

            review = {
                "review_id": "REV-DEMO",
                "client_id": "demo",
                "build_id": "BLD-DEMO",
                "direction_id": "DIR-DEMO-A",
                "coverage_ref": "experience/prototypes/a-coverage.yaml",
                "implementation_ref": "experience/prototypes/a-implementation.yaml",
                "core_runtime_ref": None,
                "demo_dataset_ref": None,
                "prototype_revision_ref": "experience/revisions/PROTO-demo-a-001.yaml",
                "review_round_ref": "feedback/rounds/ROUND-demo-a-001.yaml",
                "surface_approvals": [{"surface": "customer-app", "status": "approved"}],
                "journey_approvals": [{"journey": "browse-to-buy", "status": "approved"}],
                "live_review_sessions": ["feedback/LIVE-demo-NOWA-001.yaml"],
                "artifacts": [{
                    "artifact_id": "ART-1",
                    "surface": "customer-app",
                    "environment": "prototype",
                    "build_identity": "BLD-DEMO",
                    "approval_status": "approved",
                }],
                "status": "approved",
            }
            (project / "feedback/review.yaml").write_text(
                yaml.safe_dump(review), encoding="utf-8"
            )
            revision = {
                "revision_id": "PROTO-demo-a-001",
                "client_id": "demo",
                "direction_id": "DIR-DEMO-A",
                "sequence": 1,
                "parent_revision_ref": None,
                "source_revision": "abcdef123456",
                "build_id": "BLD-DEMO",
                "coverage_ref": "experience/prototypes/a-coverage.yaml",
                "implementation_ref": "experience/prototypes/a-implementation.yaml",
                "core_runtime_ref": None,
                "demo_dataset_ref": None,
                "surfaces": ["customer-app"],
                "journeys": ["browse-to-buy"],
                "feedback_refs": [],
                "change_refs": [],
                "created_by": "tester",
                "created_at": "2026-09-22T00:00:00Z",
                "status": "approved",
                "immutable": True,
            }
            (project / "experience/revisions/PROTO-demo-a-001.yaml").write_text(
                yaml.safe_dump(revision), encoding="utf-8"
            )
            round_value = {
                "round_id": "ROUND-demo-a-001",
                "client_id": "demo",
                "sequence": 1,
                "prototype_revision_ref": "experience/revisions/PROTO-demo-a-001.yaml",
                "review_session_ref": "feedback/review.yaml",
                "previous_round_ref": None,
                "next_revision_ref": None,
                "required_surfaces": ["customer-app"],
                "required_journeys": ["browse-to-buy"],
                "feedback_refs": [],
                "live_review_refs": ["feedback/LIVE-demo-NOWA-001.yaml"],
                "change_refs": [],
                "qa_refs": ["experience/visual-qa/qa.yaml"],
                "surface_decisions": [{"surface": "customer-app", "status": "approved"}],
                "journey_decisions": [{"journey": "browse-to-buy", "status": "approved"}],
                "outcome": "approved",
            }
            (project / "feedback/rounds/ROUND-demo-a-001.yaml").write_text(
                yaml.safe_dump(round_value), encoding="utf-8"
            )
            qa = {
                "qa_id": "VQA-DEMO",
                "client_id": "demo",
                "direction_id": "DIR-DEMO-A",
                "surface": "customer-app",
                "build_identity": "BLD-DEMO",
                "checks": [
                    {"id": check, "status": "pass", "evidence": "capture", "notes": []}
                    for check in REQUIRED_CHECKS
                ],
                "status": "passed",
            }
            (project / "experience/visual-qa/qa.yaml").write_text(
                yaml.safe_dump(qa), encoding="utf-8"
            )

            with self.assertRaisesRegex(
                FreezeError, "must be client-confirmed/closed"
            ):
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
