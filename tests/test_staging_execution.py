from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from tooling.release.candidate import create_candidate
from tooling.staging.execution import execute


def make_bundle(root: Path):
    artifact = root / "artifact.txt"
    artifact.write_text("candidate", encoding="utf-8")
    candidate = create_candidate(
        client_id="demo",
        source_revision="abcdef1234567890",
        artifact_paths=[Path("artifact.txt")],
        created_by="test",
        root=root,
    )
    cid = candidate["candidate_id"]
    manifest = {
        "manifest_id": "STGMAN-demo-abcdef123456",
        "client_id": "demo",
        "candidate_id": cid,
        "candidate_digest": candidate["artifact_digest"],
        "source_revision": candidate["source_revision"],
        "runtimes": [
            {"id":"commerce","provider":"medusa","version":"2.21.1","required":True,"healthcheck":"/health"},
            {"id":"erp","provider":"tryton","version":"8.0","required":True,"healthcheck":"/"},
        ],
        "data_imports": [
            {"id":"master-data","target":"owners","required":True,"readback":"counts"},
        ],
        "e2e_flows": ["order-to-accounting"],
        "provider_checks": ["razorpay","shiprocket","meta-whatsapp-cloud"],
        "status": "planned",
    }
    candidate_path = root / "candidate.yaml"
    manifest_path = root / "manifest.yaml"
    candidate_path.write_text(yaml.safe_dump(candidate), encoding="utf-8")
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return candidate_path, manifest_path


class StagingExecutionTests(unittest.TestCase):
    def setUp(self):
        self.names = [
            "STAGING_RUNTIME_ENDPOINTS_JSON",
            "STAGING_RUNTIME_ATTESTATIONS_JSON",
            "STAGING_IMPORT_PROBES_JSON",
            "STAGING_E2E_PROBES_JSON",
            "STAGING_OBSERVABILITY_PROBES_JSON",
            "RAZORPAY_STAGING_URL",
            "RAZORPAY_STAGING_AUTH",
            "SHIPROCKET_STAGING_URL",
            "SHIPROCKET_STAGING_AUTH",
            "WHATSAPP_STAGING_URL",
            "WHATSAPP_STAGING_AUTH",
        ]
        self.previous = {name: os.environ.get(name) for name in self.names}
        for name in self.names:
            os.environ.pop(name, None)

    def tearDown(self):
        for name, value in self.previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_missing_environment_bindings_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, manifest = make_bundle(root)
            result = execute(
                candidate_path=candidate,
                manifest_path=manifest,
                output_dir=root / "evidence",
            )
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["staging_validation"]["status"], "failed")

    @patch("tooling.staging.execution._probe_http", return_value=("pass", "HTTP 200"))
    @patch("tooling.staging.provider_probe.probe", return_value=("pass", "HTTP 200"))
    def test_all_real_environment_bindings_can_pass(self, _provider, _probe):
        os.environ["STAGING_RUNTIME_ENDPOINTS_JSON"] = '{"commerce":"https://stage/commerce","erp":"https://stage/erp"}'
        os.environ["STAGING_IMPORT_PROBES_JSON"] = '{"master-data":"https://stage/import/master"}'
        os.environ["STAGING_E2E_PROBES_JSON"] = '{"order-to-accounting":"https://stage/e2e/order"}'
        os.environ["STAGING_OBSERVABILITY_PROBES_JSON"] = '{"metric":"https://stage/metrics","trace":"https://stage/traces","error":"https://stage/errors","alert":"https://stage/alerts"}'
        os.environ["RAZORPAY_STAGING_URL"] = "https://stage/razorpay"
        os.environ["SHIPROCKET_STAGING_URL"] = "https://stage/shiprocket"
        os.environ["WHATSAPP_STAGING_URL"] = "https://stage/whatsapp"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, manifest = make_bundle(root)
            result = execute(
                candidate_path=candidate,
                manifest_path=manifest,
                output_dir=root / "evidence",
            )
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["staging_validation"]["status"], "passed")
            self.assertTrue((root / "evidence/staging-validation.yaml").exists())


if __name__ == "__main__":
    unittest.main()
