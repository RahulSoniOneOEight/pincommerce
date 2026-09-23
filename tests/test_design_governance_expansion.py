import unittest

from tooling.experience.component_lifecycle import transition
from tooling.experience.parity_gate import evaluate
from tooling.experience.promotion_gate import evaluate_promotion


class DesignGovernanceExpansionTests(unittest.TestCase):
    def test_lifecycle_requires_evidence_and_human_approval(self):
        evaluated = transition({"id":"x","status":"candidate"}, "evaluated", evidence=["benchmark"])
        approved = transition(evaluated, "approved", evidence=["quality","visual"], approver="reviewer")
        self.assertEqual(approved["status"], "approved")
        with self.assertRaises(ValueError):
            transition({"id":"y","status":"evaluated"}, "approved", evidence=["quality"])

    def test_promotion_blocks_without_impact_review_and_human_approval(self):
        result = evaluate_promotion(
            dependency={"eligibility":"eligible"},
            quality={"status":"review-ready"},
            visual={"status":"passed"},
            impact={"count":2,"reviewed":False},
            human_approval=None,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("affected-clients-not-reviewed", result["blocking_items"])

    def test_expanded_patterns_have_cross_platform_symbols(self):
        result = evaluate()
        self.assertEqual(result["status"], "passed", result["blocking_items"])
        self.assertEqual(result["patterns"], 4)


if __name__ == "__main__":
    unittest.main()
