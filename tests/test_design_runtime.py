from pathlib import Path
import unittest

from tooling.experience.runtime_acceptance import evaluate_runtime

ROOT = Path(__file__).resolve().parents[1]


class DesignRuntimeAcceptanceTests(unittest.TestCase):
    def test_five_patterns_have_cross_platform_catalog_evidence(self):
        result = evaluate_runtime(ROOT)
        self.assertEqual(result["status"], "passed", result["blocking_items"])
        self.assertEqual(result["patterns"], 5)
        self.assertEqual(result["viewports"], 3)
        self.assertIn("web:reduced-motion", result["evidence"])


if __name__ == "__main__":
    unittest.main()
