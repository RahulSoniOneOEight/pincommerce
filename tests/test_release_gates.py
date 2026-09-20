from pathlib import Path
import tempfile
from typing import Any
import unittest
import yaml

from tooling.release.candidate import create_candidate
from tooling.release.gates import GateError, verify_release_readiness
from tooling.release.hardening import (
    DEFAULT_CHECKS,
    HardeningError,
    build_hardening_evidence,
    evaluate_hardening,
)
from tooling.release.recovery import make_recovery_record
from tooling.observability.runtime import TelemetryBuffer


CANDIDATE_ID = "RC-demo-1"


def base_evidence() -> dict:
    return {
        "candidate": {
            "candidate_id": CANDIDATE_ID,
            "client_id": "demo",
            "source_revision": "abc",
            "artifact_digest": "digest",
            "environment": "staging",
            "created_by": "builder",
            "immutable": True,
            "status": "uat-passed",
        },
        "hardening": {
            "evidence_id": "HARD-1",
            "candidate_id": CANDIDATE_ID,
            "checks": [
                {"id": check_id, "status": "pass", "evidence": "ok"}
                for check_id in DEFAULT_CHECKS
            ],
            "status": "passed",
        },
        "staging": {
            "validation_id": "STG-1",
            "candidate_id": CANDIDATE_ID,
            "environment": "staging",
            "checks": [],
            "status": "passed",
        },
        "observability": {
            "evidence_id": "OBS-1",
            "candidate_id": CANDIDATE_ID,
            "signals": [],
            "status": "passed",
        },
        "uat": {
            "uat_id": "UAT-1",
            "client_id": "demo",
            "candidate_id": CANDIDATE_ID,
            "scenarios": [],
            "approved_by": "uat-owner",
            "status": "passed",
        },
        "auth": {
            "authorization_id": "AUTH-1",
            "client_id": "demo",
            "candidate_id": CANDIDATE_ID,
            "authorized_by": "release-owner",
            "decision": "approved",
            "authorized_at": "2026-09-19T00:00:00Z",
        },
    }


class ReleaseGateTests(unittest.TestCase):
    def _write_bundle(self, root: Path, evidence: dict | None = None) -> dict[str, Path]:
        values = evidence or base_evidence()
        paths = {}
        for name, value in values.items():
            path = root / f"{name}.yaml"
            path.write_text(yaml.safe_dump(value), encoding="utf-8")
            paths[name] = path
        return paths

    def _verify(self, paths: dict[str, Path], **overrides):
        kwargs: dict[str, Any] = dict(
            candidate_path=paths["candidate"],
            hardening_path=paths["hardening"],
            staging_path=paths["staging"],
            observability_path=paths.get("observability"),
            uat_path=paths["uat"],
            authorization_path=paths["auth"],
        )
        kwargs.update(overrides)
        return verify_release_readiness(**kwargs)

    def test_candidate_digest_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "artifact.txt"
            artifact.write_text("release-artifact", encoding="utf-8")

            first = create_candidate(
                client_id="demo",
                source_revision="abcdef1234567890",
                artifact_paths=[Path("artifact.txt")],
                created_by="tester",
                root=root,
            )
            second = create_candidate(
                client_id="demo",
                source_revision="abcdef1234567890",
                artifact_paths=[Path("artifact.txt")],
                created_by="tester",
                root=root,
            )
            self.assertEqual(first["artifact_digest"], second["artifact_digest"])
            self.assertTrue(first["immutable"])

    def test_release_requires_exact_candidate_and_human_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_bundle(Path(tmp))
            result = self._verify(paths)
            self.assertTrue(result["ready"])
            self.assertEqual(result["authorized_by"], "release-owner")

            auth = base_evidence()["auth"]
            auth["candidate_id"] = "RC-other"
            paths["auth"].write_text(yaml.safe_dump(auth), encoding="utf-8")
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_without_staging_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_bundle(Path(tmp))
            staging = base_evidence()["staging"]
            staging["status"] = "draft"
            paths["staging"].write_text(yaml.safe_dump(staging), encoding="utf-8")
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_when_candidate_not_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = base_evidence()
            evidence["candidate"]["immutable"] = False
            paths = self._write_bundle(Path(tmp), evidence)
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_on_empty_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = base_evidence()
            evidence["candidate"]["artifact_digest"] = ""
            paths = self._write_bundle(Path(tmp), evidence)
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_on_non_promotable_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = base_evidence()
            evidence["candidate"]["status"] = "created"
            paths = self._write_bundle(Path(tmp), evidence)
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_when_observability_not_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = base_evidence()
            evidence["observability"]["status"] = "failed"
            paths = self._write_bundle(Path(tmp), evidence)
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_when_uat_has_no_approver(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = base_evidence()
            evidence["uat"]["approved_by"] = None
            paths = self._write_bundle(Path(tmp), evidence)
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_when_hardening_missing_required_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = base_evidence()
            evidence["hardening"]["checks"] = [
                {"id": "unit-tests", "status": "pass", "evidence": "ok"}
            ]
            evidence["hardening"]["status"] = "passed"
            paths = self._write_bundle(Path(tmp), evidence)
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_release_fails_when_hardening_omits_a_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = base_evidence()
            evidence["hardening"]["checks"] = [
                check
                for check in evidence["hardening"]["checks"]
                if check["id"] != "security-secrets"
            ]
            paths = self._write_bundle(Path(tmp), evidence)
            with self.assertRaises(GateError):
                self._verify(paths)

    def test_reference_fixture_bundle_passes_release_gate(self):
        base = Path(__file__).resolve().parents[1] / "client-projects" / "reference-retail"
        result = verify_release_readiness(
            candidate_path=base / "release/candidates/RC-reference-retail-ref001.yaml",
            hardening_path=base / "release/hardening/RC-reference-retail-ref001.yaml",
            staging_path=base / "release/staging/RC-reference-retail-ref001.yaml",
            observability_path=base / "release/observability/RC-reference-retail-ref001.yaml",
            uat_path=base / "uat/RC-reference-retail-ref001.yaml",
            authorization_path=base / "release/production-authorization.yaml",
        )
        self.assertTrue(result["ready"])
        self.assertEqual(result["candidate_id"], "RC-reference-retail-ref001")

    def test_recovery_plan(self):
        record = make_recovery_record(
            recovery_id="REC-1",
            release_id="REL-1",
            reason="smoke failure",
            action="rollback",
            target_candidate_id="RC-previous",
        )
        self.assertEqual(record["status"], "planned")
        self.assertEqual(record["action"], "rollback")

    def test_observability_buffer(self):
        telemetry = TelemetryBuffer()
        telemetry.metric("http.latency", ms=25)
        telemetry.trace("order.to.erp", correlation_id="corr-1")
        telemetry.error("provider.failure", provider="tryton")
        snapshot = telemetry.snapshot()
        self.assertEqual(len(snapshot), 3)
        self.assertEqual(snapshot[1]["kind"], "trace")


class HardeningPolicyTests(unittest.TestCase):
    def test_missing_required_check_is_blocking(self):
        evidence = build_hardening_evidence("RC-demo-1", {"contract-validation": ("pass", "ci")})
        self.assertEqual(evidence["status"], "failed")

    def test_all_pass_is_accepted(self):
        results = {check: ("pass", "ok") for check in _all_checks()}
        evidence = build_hardening_evidence("RC-demo-1", results)
        self.assertEqual(evidence["status"], "passed")

    def test_warning_is_blocking_by_default(self):
        results = {check: ("pass", "ok") for check in _all_checks()}
        results["dependency-vulnerability"] = ("warning", "scan deferred")
        evidence = build_hardening_evidence("RC-demo-1", results)
        self.assertEqual(evidence["status"], "failed")
        blocking = evaluate_hardening(evidence)["blocking"]
        self.assertIn("dependency-vulnerability", blocking)

    def test_warning_is_non_blocking_when_declared(self):
        results = {check: ("pass", "ok") for check in _all_checks()}
        results["dependency-vulnerability"] = ("warning", "scan deferred")
        evidence = build_hardening_evidence(
            "RC-demo-1", results, non_blocking=["dependency-vulnerability"]
        )
        self.assertEqual(evidence["status"], "passed")
        self.assertEqual(evaluate_hardening(evidence)["status"], "passed")

    def test_fail_is_blocking(self):
        results = {check: ("pass", "ok") for check in _all_checks()}
        results["unit-tests"] = ("fail", "red")
        evidence = build_hardening_evidence("RC-demo-1", results)
        self.assertEqual(evidence["status"], "failed")

    def test_unknown_status_is_rejected(self):
        results = {check: ("pass", "ok") for check in _all_checks()}
        results["unit-tests"] = ("skipped", "n/a")
        with self.assertRaises(HardeningError):
            build_hardening_evidence("RC-demo-1", results)

    def test_unknown_check_id_is_rejected(self):
        with self.assertRaises(HardeningError):
            build_hardening_evidence("RC-demo-1", {"not-a-check": ("pass", "ok")})

    def test_evaluate_rejects_unknown_status(self):
        evidence = {
            "candidate_id": "RC-demo-1",
            "checks": [{"id": "unit-tests", "status": "skipped"}],
            "status": "passed",
        }
        with self.assertRaises(HardeningError):
            evaluate_hardening(evidence)

    def test_evaluate_missing_required_check_is_blocking(self):
        evidence = {
            "candidate_id": "RC-demo-1",
            "checks": [{"id": "unit-tests", "status": "pass"}],
            "status": "passed",
        }
        result = evaluate_hardening(evidence)
        self.assertEqual(result["status"], "failed")
        self.assertIn("security-secrets", result["missing_checks"])

    def test_evaluate_empty_checks_is_blocking(self):
        result = evaluate_hardening(
            {"candidate_id": "RC-demo-1", "checks": [], "status": "passed"}
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["missing_checks"], list(DEFAULT_CHECKS))

    def test_evaluate_treats_unknown_check_id_as_blocking(self):
        evidence = {
            "candidate_id": "RC-demo-1",
            "checks": [{"id": "mystery-check", "status": "pass"}],
            "status": "passed",
        }
        result = evaluate_hardening(evidence)
        self.assertEqual(result["status"], "failed")
        self.assertIn("mystery-check", result["unknown_checks"])


def _all_checks() -> list[str]:
    from tooling.release.hardening import DEFAULT_CHECKS

    return list(DEFAULT_CHECKS)


if __name__ == "__main__":
    unittest.main()
