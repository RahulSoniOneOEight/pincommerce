import unittest

from tooling.experience.quality import DesignQualityError, evaluate_quality, select_tournament_winner


WEIGHTS = {
    "functional_fit": 20,
    "visual_quality": 15,
    "information_hierarchy": 15,
    "interaction_quality": 10,
    "responsive_fit": 10,
    "accessibility": 10,
    "brand_alignment": 10,
    "performance": 5,
    "reusability": 5,
}


def scores(value: float):
    return {
        key: (value, [f"evidence:{key}"], key in {"functional_fit", "responsive_fit", "accessibility", "performance"})
        for key in WEIGHTS
    }


class DesignQualityTests(unittest.TestCase):
    def test_above_threshold_is_review_ready(self):
        result = evaluate_quality(
            client_id="demo",
            target="product-card-a",
            scores=scores(90),
            weights=WEIGHTS,
        )
        self.assertEqual(result["score"], 90)
        self.assertEqual(result["status"], "review-ready")

    def test_below_threshold_fails(self):
        result = evaluate_quality(
            client_id="demo",
            target="product-card-b",
            scores=scores(70),
            weights=WEIGHTS,
        )
        self.assertEqual(result["status"], "failed")

    def test_ai_only_scores_cannot_pass(self):
        values = {key: (95, [f"visual:{key}"], False) for key in WEIGHTS}
        result = evaluate_quality(
            client_id="demo",
            target="product-card-c",
            scores=values,
            weights=WEIGHTS,
        )
        self.assertEqual(result["status"], "failed")

    def test_tournament_selects_highest_eligible_score(self):
        a = evaluate_quality(client_id="demo", target="A", scores=scores(84), weights=WEIGHTS)
        b = evaluate_quality(client_id="demo", target="B", scores=scores(91), weights=WEIGHTS)
        c = evaluate_quality(client_id="demo", target="C", scores=scores(78), weights=WEIGHTS)
        self.assertEqual(select_tournament_winner([a, b, c])["target"], "B")

    def test_missing_criteria_is_rejected(self):
        values = scores(90)
        values.pop("accessibility")
        with self.assertRaises(DesignQualityError):
            evaluate_quality(client_id="demo", target="A", scores=values, weights=WEIGHTS)


if __name__ == "__main__":
    unittest.main()
