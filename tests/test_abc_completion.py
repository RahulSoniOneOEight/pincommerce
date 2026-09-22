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
from tooling.review.visual_qa import evaluate_visual_qa, plan_visual_qa
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
            for folder in ("solution", "derived", "feedback", "experience/directions", "experience/visual-qa"):
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
            (project / "feedback/review.yaml").write_text(yaml.safe_dump(review), encoding="utf-8")
            qa = {
                "qa_id": "VQA-DEMO", "client_id": "demo", "direction_id": "DIR-DEMO-A",
                "surface": "customer-app", "build_identity": "BLD-DEMO",
                "checks": [{"id": "visual", "status": "pass", "evidence": "capture", "notes": []}],
                "status": "passed",
            }
            (project / "experience/visual-qa/qa.yaml").write_text(yaml.safe_dump(qa), encoding="utf-8")

            baseline = build_scope_baseline(
                "demo", review_file="review.yaml", visual_qa_files=["qa.yaml"],
                approved_by="client-owner", approved_at="2026-09-22T00:00:00Z", root=root
            )
            self.assertTrue(baseline["immutable"])
            self.assertEqual(validate_document(baseline, "scope-baseline"), [])

            review["status"] = "in-review"
            (project / "feedback/review.yaml").write_text(yaml.safe_dump(review), encoding="utf-8")
            with self.assertRaises(FreezeError):
                build_scope_baseline(
                    "demo", review_file="review.yaml", visual_qa_files=["qa.yaml"],
                    approved_by="client-owner", approved_at="2026-09-22T00:00:00Z", root=root
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
