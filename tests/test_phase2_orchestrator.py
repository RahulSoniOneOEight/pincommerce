from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from tooling.orchestrator.phase2 import assess


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


class Phase2OrchestratorTests(unittest.TestCase):
    def test_missing_evidence_is_blocking_not_fabricated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = assess("demo", root)
            self.assertEqual(result["status"], "phase2-not-ready")
            self.assertFalse(result["human_gates"]["uat"])
            self.assertFalse(result["human_gates"]["production_authorization"])
            self.assertIn("phase1-handoff", result["blocking_items"])

    def test_human_gates_and_exact_candidate_are_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "client-projects" / "demo"
            dump(project / "experience" / "integrated-prototype-readiness.yaml", {"integrated-prototype-ready": True})
            dump(project / "production" / "production-readiness.yaml", {"status": "production-ready"})
            cid = "RC-demo-1"
            dump(project / "release" / "candidates" / f"{cid}.yaml", {
                "candidate_id": cid, "immutable": True, "artifact_digest": "sha256:test",
                "environment": "staging", "status": "staging-passed"
            })
            result = assess("demo", root)
            self.assertEqual(result["status"], "phase2-not-ready")
            self.assertIn("uat-human-gate", result["blocking_items"])
            self.assertIn("production-authorization-human-gate", result["blocking_items"])

    @patch("tooling.orchestrator.phase2.verify_release_readiness")
    @patch("tooling.orchestrator.phase2.evaluate_hardening", return_value={"status": "passed"})
    def test_authorized_candidate_reaches_release_authorized(self, _hardening, verify):
        verify.return_value = {"ready": True}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "client-projects" / "demo"
            cid = "RC-demo-1"
            dump(project / "experience" / "integrated-prototype-readiness.yaml", {"integrated-prototype-ready": True})
            dump(project / "production" / "production-readiness.yaml", {"status": "production-ready"})
            dump(project / "release" / "candidates" / f"{cid}.yaml", {"candidate_id": cid, "immutable": True, "artifact_digest": "sha256:test"})
            dump(project / "release" / "hardening" / f"{cid}.yaml", {"candidate_id": cid, "status": "passed"})
            dump(project / "release" / "staging" / f"{cid}.yaml", {"candidate_id": cid, "status": "passed"})
            dump(project / "release" / "observability" / f"{cid}.yaml", {
                "candidate_id": cid, "status": "passed",
                "signals": [{"kind": kind, "status": "pass"} for kind in ("metric", "trace", "error", "alert")]
            })
            dump(project / "uat" / f"{cid}.yaml", {"candidate_id": cid, "status": "passed", "approved_by": "human"})
            dump(project / "release" / "production-authorization.yaml", {"candidate_id": cid, "decision": "approved", "authorized_by": "human"})
            result = assess("demo", root)
            self.assertEqual(result["status"], "release-authorized")
            self.assertTrue(result["human_gates"]["uat"])
            self.assertTrue(result["human_gates"]["production_authorization"])


if __name__ == "__main__":
    unittest.main()
