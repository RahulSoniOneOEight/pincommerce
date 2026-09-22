from pathlib import Path
import tempfile
import unittest

import yaml

from tooling.contracts.validator import validate_document
from tooling.onboarding.abc_completion import (
    architecture_decisions,
    build_integration_map,
    build_truth_register,
    classification_evidence,
    enrich_capability_gap,
)
from tooling.review.freeze import FreezeError, build_scope_baseline
from tooling.review.visual_qa import REQUIRED_CHECKS, evaluate_visual_qa, plan_visual_qa
from tooling.experience.coverage import build_coverage
from tooling.review.impact import analyze_change


class ABCCompletionTests(unittest.TestCase):
    def test_truth_register_separates_facts_assumptions_and_unknowns(self):
        value = build_truth_register({
            "client_id": "demo",
            "industry": "retail",
            "business_models": ["d2c"],
            "source_refs": ["brief.pdf"],
            "assumptions": ["warehouse count is stable"],
            "open_questions": ["Who approves refunds?"],
        })
        classes = {item["classification"] for item in value["records"]}
        self.assertEqual(value["status"], "needs-input")
        self.assertIn("fact", classes)
        self.assertIn("assumption", classes)
        self.assertIn("unknown", classes)
        self.assertEqual(validate_document(value, "truth-register"), [])

    def test_classification_is_evidence_backed(self):
        value = classification_evidence(["d2c", "b2b"], ["d2c-commerce", "b2b-commerce"])
        self.assertEqual(value["confidence"], 1.0)
        self.assertEqual(value["method"], "deterministic-rules")
        self.assertEqual(len(value["evidence"]), 2)

    def test_gap_analysis_prioritizes_core(self):
        value = enrich_capability_gap({
            "client_id": "demo",
            "core_missing": ["checkout"],
            "recommended_missing": ["loyalty"],
            "not_in_reference_baseline": ["special-flow"],
        })
        by_capability = {item["capability"]: item for item in value["items"]}
        self.assertEqual(by_capability["checkout"]["severity"], "high")
        self.assertEqual(by_capability["loyalty"]["priority"], 2)
        self.assertEqual(by_capability["special-flow"]["gap_type"], "client-specific")
        self.assertEqual(value["blocking_count"], 1)

    def test_integration_map_includes_provider_and_operational_metadata(self):
        value = build_integration_map({
            "client_id": "demo",
            "required_integrations": ["payment", "logistics", "whatsapp"],
        })
        self.assertEqual(validate_document(value, "integration-map"), [])
        items = {item["id"]: item for item in value["integrations"]}
        self.assertEqual(items["payment"]["provider_candidates"], ["razorpay", "cashfree"])
        self.assertEqual(items["logistics"]["criticality"], "high")
        self.assertEqual(items["whatsapp"]["fallback_strategy"], "queue-and-retry")

    def test_architecture_decisions_are_explicit(self):
        decisions = architecture_decisions("demo", {
            "providers": {
                "commerce": {"type": "commerce", "provider": "medusa"},
                "erp": {"type": "erp", "provider": "tryton"},
            }
        })
        self.assertEqual(len(decisions), 2)
        for item in decisions:
            self.assertEqual(validate_document(item, "architecture-decision"), [])

    def test_scope_freeze_requires_approved_review_and_passed_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "client-projects" / "demo"
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
            truth = {
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
            }
            (project / "derived/truth-register.yaml").write_text(
                yaml.safe_dump(truth), encoding="utf-8"
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
            implementation = {
                "implementation_id": "IMP-demo-a",
                "client_id": "demo",
                "direction_id": "DIR-DEMO-A",
                "surfaces": [{
                    "surface": "customer-app",
                    "runtime_ref": "apps/prototype_app",
                    "screens": [
                        {"id": item, "status": "implemented", "evidence_ref": f"app#{item}"}
                        for item in surface["screens"]
                    ],
                    "components": [
                        {"id": item, "status": "implemented", "evidence_ref": f"ui#{item}"}
                        for item in surface["components"]
                    ],
                    "states": [
                        {"id": item, "status": "implemented", "evidence_ref": f"fixture#{item}"}
                        for item in surface["states"]
                    ],
                    "status": "complete",
                }],
                "status": "complete",
            }
            (project / "experience/prototypes/a-implementation.yaml").write_text(
                yaml.safe_dump(implementation), encoding="utf-8"
            )

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
                "live_review_refs": [],
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

            baseline = build_scope_baseline(
                "demo",
                review_file="review.yaml",
                visual_qa_files=["qa.yaml"],
                approved_by="client-owner",
                approved_at="2026-09-22T00:00:00Z",
                root=root,
            )
            self.assertTrue(baseline["immutable"])
            self.assertEqual(baseline["approved_surfaces"], ["customer-app"])
            self.assertEqual(baseline["approved_journeys"], ["browse-to-buy"])
            self.assertEqual(
                baseline["prototype_implementation_ref"],
                "experience/prototypes/a-implementation.yaml",
            )
            self.assertEqual(validate_document(baseline, "scope-baseline"), [])

            review["status"] = "in-review"
            (project / "feedback/review.yaml").write_text(
                yaml.safe_dump(review), encoding="utf-8"
            )
            with self.assertRaises(FreezeError):
                build_scope_baseline(
                    "demo",
                    review_file="review.yaml",
                    visual_qa_files=["qa.yaml"],
                    approved_by="client-owner",
                    approved_at="2026-09-22T00:00:00Z",
                    root=root,
                )


    def test_visual_qa_planner_covers_business_and_visual_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qa_dir = root / "client-projects/demo/experience/visual-qa"
            qa_dir.mkdir(parents=True)
            capture = {
                "capture_id": "CAP-DEMO", "client_id": "demo", "build_id": "BLD-DEMO",
                "direction_id": "DIR-DEMO-A",
                "targets": [
                    {"surface": "customer-app", "runtime": "flutter", "viewport": "390x844",
                     "state": "default", "output": "review/demo.png"},
                    {"surface": "customer-app", "runtime": "flutter", "viewport": "390x844",
                     "state": "failure", "output": "review/demo-failure.png"},
                ],
                "status": "planned",
            }
            (qa_dir / "capture.yaml").write_text(yaml.safe_dump(capture), encoding="utf-8")
            planned = plan_visual_qa("demo", "capture.yaml", root)
            record = next(iter(planned.values()))
            ids = {item["id"] for item in record["checks"]}
            self.assertIn("business-rules", ids)
            self.assertIn("journey-coverage", ids)
            for item in record["checks"]:
                item["status"] = "pass"
            evaluated = evaluate_visual_qa(record)
            self.assertEqual(evaluated["status"], "passed")

    def test_change_impact_uses_dependency_entity_and_integration_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            derived = root / "client-projects/demo/derived"
            derived.mkdir(parents=True)
            (derived / "dependency-map.yaml").write_text(
                "client_id: demo\ncritical_cross_domain_flows:\n"
                "  - id: checkout-to-accounting\n"
                "    domains: [experience, commerce, integration, erp]\n",
                encoding="utf-8",
            )
            (derived / "entity-map.yaml").write_text(
                "client_id: demo\nentities:\n"
                "  order: {owner_capability: checkout}\n",
                encoding="utf-8",
            )
            (derived / "integration-map.yaml").write_text(
                "client_id: demo\nintegrations:\n"
                "  - {id: payment, domain: payments, provider_candidates: [razorpay], direction: bidirectional, criticality: critical, data_classes: [operational], fallback_strategy: queue-and-retry}\n",
                encoding="utf-8",
            )
            impact = analyze_change("demo", ["checkout"], ["customer-app"], root)
            self.assertIn("commerce", impact["affected_domains"])
            self.assertIn("order", impact["affected_entities"])
            self.assertTrue(impact["approval_required"])
            self.assertIn("e2e", impact["required_tests"])


if __name__ == "__main__":
    unittest.main()
