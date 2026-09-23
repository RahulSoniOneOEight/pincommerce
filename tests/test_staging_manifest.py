from pathlib import Path
import tempfile
import unittest

from tooling.staging.manifest import build_candidate_and_manifest

ROOT = Path(__file__).resolve().parents[1]


class StagingManifestTests(unittest.TestCase):
    def test_reference_retail_manifest_is_derived_from_phase_d(self):
        candidate, manifest = build_candidate_and_manifest(
            "reference-retail",
            "abcdef1234567890",
            created_by="test",
            root=ROOT,
        )
        self.assertTrue(candidate["immutable"])
        self.assertEqual(manifest["candidate_id"], candidate["candidate_id"])
        self.assertEqual(manifest["candidate_digest"], candidate["artifact_digest"])
        runtime_ids = {item["id"] for item in manifest["runtimes"]}
        self.assertIn("commerce", runtime_ids)
        self.assertIn("erp", runtime_ids)
        self.assertIn("database", runtime_ids)
        self.assertEqual(
            set(manifest["provider_checks"]),
            {"razorpay", "shiprocket", "meta-whatsapp-cloud"},
        )
        self.assertTrue(manifest["e2e_flows"])


if __name__ == "__main__":
    unittest.main()
