from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.release.gates import GateError, verify_release_readiness
from tooling.release.hardening import evaluate_hardening

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _check(check_id: str, ok: bool, evidence: list[str]) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if ok else "not-ready", "evidence": evidence}


def assess(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    phase1 = _load(project / "experience" / "integrated-prototype-readiness.yaml")
    phase1_ok = bool(phase1 and phase1.get("integrated-prototype-ready") is True)
    checks.append(_check("phase1-handoff", phase1_ok, [
        "experience/integrated-prototype-readiness.yaml" if phase1 else "missing integrated prototype readiness"
    ]))

    readiness = _load(project / "production" / "production-readiness.yaml")
    readiness_ok = bool(readiness and readiness.get("status") in {"ready", "production-ready"})
    checks.append(_check("production-readiness", readiness_ok, [
        "production/production-readiness.yaml" if readiness else "missing production readiness"
    ]))

    candidates = sorted((project / "release" / "candidates").glob("*.yaml")) if (project / "release" / "candidates").exists() else []
    candidate_path = candidates[-1] if candidates else None
    candidate = _load(candidate_path) if candidate_path else None
    candidate_id = candidate.get("candidate_id") if candidate else None
    candidate_ok = bool(candidate and candidate.get("immutable") is True and candidate.get("artifact_digest"))
    checks.append(_check("immutable-candidate", candidate_ok, [
        str(candidate_path.relative_to(project)) if candidate_path else "missing release candidate"
    ]))

    hardening_path = project / "release" / "hardening" / f"{candidate_id}.yaml" if candidate_id else None
    hardening = _load(hardening_path) if hardening_path else None
    hardening_ok = False
    if hardening:
        try:
            hardening_ok = evaluate_hardening(hardening).get("status") == "passed" and hardening.get("status") == "passed"
        except Exception:
            hardening_ok = False
    checks.append(_check("hardening", hardening_ok, [
        str(hardening_path.relative_to(project)) if hardening_path and hardening_path.exists() else "missing/pending hardening evidence"
    ]))

    staging_path = project / "release" / "staging" / f"{candidate_id}.yaml" if candidate_id else None
    staging = _load(staging_path) if staging_path else None
    staging_ok = bool(staging and staging.get("candidate_id") == candidate_id and staging.get("status") == "passed")
    checks.append(_check("staging", staging_ok, [
        str(staging_path.relative_to(project)) if staging_path and staging_path.exists() else "missing staging evidence"
    ]))

    observability_path = project / "release" / "observability" / f"{candidate_id}.yaml" if candidate_id else None
    observability = _load(observability_path) if observability_path else None
    signal_kinds = {row.get("kind") for row in (observability or {}).get("signals", []) if row.get("status") == "pass"}
    observability_ok = bool(observability and observability.get("candidate_id") == candidate_id and observability.get("status") == "passed" and {"metric", "trace", "error", "alert"} <= signal_kinds)
    checks.append(_check("observability", observability_ok, [
        str(observability_path.relative_to(project)) if observability_path and observability_path.exists() else "missing observability evidence"
    ]))

    uat_path = project / "uat" / f"{candidate_id}.yaml" if candidate_id else None
    uat = _load(uat_path) if uat_path else None
    uat_ok = bool(uat and uat.get("candidate_id") == candidate_id and uat.get("status") == "passed" and uat.get("approved_by"))
    checks.append(_check("uat-human-gate", uat_ok, [
        str(uat_path.relative_to(project)) if uat_path and uat_path.exists() else "missing human-approved UAT"
    ]))

    auth_path = project / "release" / "production-authorization.yaml"
    auth = _load(auth_path)
    auth_ok = bool(auth and auth.get("candidate_id") == candidate_id and auth.get("decision") == "approved" and auth.get("authorized_by"))
    checks.append(_check("production-authorization-human-gate", auth_ok, [
        "release/production-authorization.yaml" if auth else "missing human production authorization"
    ]))

    exact_release_ready = False
    if all([candidate_path, hardening_path, uat_path, staging_path]) and auth_path.exists():
        try:
            verify_release_readiness(
                candidate_path=candidate_path,
                hardening_path=hardening_path,
                uat_path=uat_path,
                authorization_path=auth_path,
                staging_path=staging_path,
                observability_path=observability_path if observability_path and observability_path.exists() else None,
            )
            exact_release_ready = True
        except (GateError, OSError, ValueError):
            exact_release_ready = False
    checks.append(_check("exact-candidate-release-gate", exact_release_ready, [
        "candidate, hardening, staging, observability, UAT and authorization must reference the exact same candidate"
    ]))

    release_files = sorted((project / "release" / "releases").glob("*.yaml")) if (project / "release" / "releases").exists() else []
    release = _load(release_files[-1]) if release_files else None
    released = bool(release and release.get("candidate_id") == candidate_id)
    checks.append(_check("release-record", released, [
        str(release_files[-1].relative_to(project)) if release_files else "missing release record"
    ]))

    ops_dir = project / "production" / "ops"
    operating = bool(released and ops_dir.exists() and any(ops_dir.glob("*.yaml")))
    checks.append(_check("operations-evidence", operating, [
        "production/ops" if ops_dir.exists() else "missing operations evidence"
    ]))

    for row in checks:
        if row["status"] != "pass":
            blockers.append(row["id"])

    if operating:
        status = "operating"
    elif exact_release_ready:
        status = "release-authorized"
    elif phase1_ok and readiness_ok and candidate_ok and hardening_ok and staging_ok and observability_ok:
        status = "production-ready"
    else:
        status = "phase2-not-ready"

    return {
        "client_id": client_id,
        "candidate_id": candidate_id,
        "checks": checks,
        "blocking_items": blockers,
        "human_gates": {"uat": uat_ok, "production_authorization": auth_ok},
        "status": status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess Phase 2 production and operations readiness without fabricating evidence")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = assess(args.client, args.root)
    if args.write:
        path = args.root / "client-projects" / args.client / "release" / "phase2-readiness.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    print(yaml.safe_dump(result, sort_keys=False))
    if args.check and result["status"] not in {"release-authorized", "operating"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
