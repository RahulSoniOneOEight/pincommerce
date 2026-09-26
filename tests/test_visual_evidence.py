import unittest

from tooling.experience.visual_evidence import evaluate_evidence
from tooling.experience.visual_tournament import select_review_winner


class VisualEvidenceTests(unittest.TestCase):
    def policy(self):
        return {
            "story_ids": {"product-card": "commerce-productcard--default"},
            "viewports": {"mobile-390": {"width": 390, "height": 844}},
            "accessibility": {"max_critical": 0, "max_serious": 0},
            "performance": {"max_dom_content_loaded_ms": 2500, "max_transfer_bytes": 1500000},
        }

    def test_evidence_requires_render_hash_accessibility_and_performance(self):
        result = evaluate_evidence({"captures": [{
            "pattern": "product-card", "viewport_id": "mobile-390",
            "screenshot_sha256": "sha256:abc", "dom_fingerprint": "sha256:def",
            "accessibility": {"critical": 0, "serious": 0},
            "performance": {"dom_content_loaded_ms": 500, "transfer_bytes": 10000},
        }]}, self.policy())
        self.assertEqual(result["status"], "passed")

    def test_ci_capture_wall_time_is_not_a_component_performance_gate(self):
        payload = {"captures": [{
            "pattern": "product-card", "viewport_id": "mobile-390",
            "screenshot_sha256": "sha256:abc", "dom_fingerprint": "sha256:def",
            "accessibility": {"critical": 0, "serious": 0},
            "performance": {"dom_content_loaded_ms": 500, "transfer_bytes": 10000},
            "elapsed_ms": 999999,
        }]}
        policy = self.policy()
        policy["performance"]["max_component_runtime_ms"] = 1
        self.assertEqual(evaluate_evidence(payload, policy)["status"], "passed")

    def test_tournament_filters_ineligible_and_requires_human_review(self):
        result = select_review_winner([
            {"id": "a", "dependency_eligibility": "eligible", "deterministic_evidence": True,
             "dimensions": {"accessibility": 95, "performance": 90, "visual-regression": 90, "completeness": 100}},
            {"id": "b", "dependency_eligibility": "blocked", "deterministic_evidence": True,
             "dimensions": {"accessibility": 100, "performance": 100, "visual-regression": 100, "completeness": 100}},
        ], {"accessibility": 30, "performance": 25, "visual-regression": 25, "completeness": 20})
        self.assertEqual(result["winner"]["id"], "a")
        self.assertEqual(result["status"], "human-review-required")


if __name__ == "__main__":
    unittest.main()
