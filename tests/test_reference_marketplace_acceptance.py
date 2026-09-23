from pathlib import Path
import unittest

from tooling.marketplace.reference_acceptance import evaluate_reference_marketplace

ROOT = Path(__file__).resolve().parents[1]


class ReferenceMarketplaceAcceptanceTests(unittest.TestCase):
    def test_reference_marketplace_is_governed_across_a_to_d(self):
        result = evaluate_reference_marketplace(ROOT)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["blocking_items"], [])
        self.assertTrue(all(value == "pass" for value in result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
