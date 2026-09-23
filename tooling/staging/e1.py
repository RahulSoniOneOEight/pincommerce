from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_STAGING_CHECKS = (
    "candidate-integrity",
    "runtime-health",
    "data-import-readback",
    "cross-system-e2e",
    "provider-sandbox",
    "observability",
)


class E1Error(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise E1Error(f"Missing E1 evidence: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise E1Error(f"Expected mapping in {path}")
    return value


def _require_candidate(document: dict[str, Any], candidate_id: str, label: str) -> list[str]:
    return [] if document.get("candidate_id") == candidate_id else [f"{label} candidate mismatch"]


def evaluate_e1(
    *,
    candidate: dict[str, Any],
    manifest: dict[str, Any],
    runtime_evidence: dict[str, Any],
    import_evidence: dict[str, Any],
    e2e_evidence: dict[str, Any],
    provider_evidence: dict[str, Any],
    observability: dict[str, Any],
) -> dict[str, Any]:
    for contract, document in (
        ("release-candidate", candidate),
        ("staging-manifest", manifest),
        ("provider-sandbox-evidence", provider_evidence),
        ("observability-evidence", observability),
    ):
        errors = validate_document(document, contract)
        if errors:
            raise E1Error(f"Invalid {contract}: " + "; ".join(errors))

    candidate_id = candidate["candidate_id"]
    checks: list[dict[str, Any]] = []

    candidate_issues: list[str] = []
    if candidate.get("immutable") is not True:
        candidate_issues.append("candidate is not immutable")
    if not candidate.get("artifact_digest"):
        candidate_issues.append("candidate digest missing")
    if manifest.get("candidate_id") != candidate_id:
        candidate_issues.append("manifest candidate mismatch")
    if manifest.get("candidate_digest") != candidate.get("artifact_digest"):
        candidate_issues.append("manifest digest mismatch")
    if manifest.get("source_revision") != candidate.get("source_revision"):
        candidate_issues.append("manifest source revision mismatch")
    checks.append({"id":"candidate-integrity","status":"pass" if not candidate_issues else "fail","details":candidate_issues})

    runtime_issues = _require_candidate(runtime_evidence, candidate_id, "runtime evidence")
    expected = {item["id"] for item in manifest.get("runtimes", []) if item.get("required")}
    actual = {
        item.get("id") for item in runtime_evidence.get("runtimes", [])
        if item.get("status") == "pass"
    }
    missing = sorted(expected - actual)
    runtime_issues.extend(f"runtime not healthy: {item}" for item in missing)
    checks.append({"id":"runtime-health","status":"pass" if not runtime_issues else "fail","details":runtime_issues})

    import_issues = _require_candidate(import_evidence, candidate_id, "import evidence")
    expected_imports = {item["id"] for item in manifest.get("data_imports", []) if item.get("required")}
    passed_imports = {
        item.get("id") for item in import_evidence.get("imports", [])
        if item.get("status") == "pass" and item.get("readback_status") == "pass"
    }
    for item in sorted(expected_imports - passed_imports):
        import_issues.append(f"import/readback not passed: {item}")
    checks.append({"id":"data-import-readback","status":"pass" if not import_issues else "fail","details":import_issues})

    e2e_issues = _require_candidate(e2e_evidence, candidate_id, "E2E evidence")
    expected_flows = set(manifest.get("e2e_flows", []))
    passed_flows = {
        item.get("id") for item in e2e_evidence.get("flows", [])
        if item.get("status") == "pass"
    }
    for item in sorted(expected_flows - passed_flows):
        e2e_issues.append(f"E2E flow not passed: {item}")
    checks.append({"id":"cross-system-e2e","status":"pass" if not e2e_issues else "fail","details":e2e_issues})

    provider_issues = _require_candidate(provider_evidence, candidate_id, "provider evidence")
    required_providers = set(manifest.get("provider_checks", []))
    provider_rows = {item.get("id"): item for item in provider_evidence.get("providers", [])}
    for provider in sorted(required_providers):
        row = provider_rows.get(provider)
        if not row or row.get("status") != "pass":
            provider_issues.append(f"provider sandbox not passed: {provider}")
    if provider_evidence.get("status") != "passed":
        provider_issues.append("provider evidence status is not passed")
    checks.append({"id":"provider-sandbox","status":"pass" if not provider_issues else "fail","details":provider_issues})

    obs_issues = _require_candidate(observability, candidate_id, "observability evidence")
    if observability.get("status") != "passed":
        obs_issues.append("observability status is not passed")
    required_signal_kinds = {"metric","trace","error","alert"}
    passing_signal_kinds = {
        item.get("kind") for item in observability.get("signals", [])
        if item.get("status") == "pass"
    }
    for kind in sorted(required_signal_kinds - passing_signal_kinds):
        obs_issues.append(f"missing passing observability signal: {kind}")
    checks.append({"id":"observability","status":"pass" if not obs_issues else "fail","details":obs_issues})

    blockers = [
        f"{check['id']}: {detail}"
        for check in checks if check["status"] != "pass"
        for detail in check["details"]
    ]
    staging = {
        "validation_id": f"STG-{candidate_id}",
        "candidate_id": candidate_id,
        "environment": "staging",
        "checks": [
            {
                "id": check["id"],
                "status": check["status"],
                "evidence": "; ".join(check["details"]) if check["details"] else "verified",
            }
            for check in checks
        ],
        "status": "passed" if not blockers else "failed",
    }
    return {"checks": checks, "blocking_items": blockers, "staging_validation": staging, "status": "passed" if not blockers else "blocked"}


def evaluate_paths(
    *,
    candidate_path: Path,
    manifest_path: Path,
    runtime_evidence_path: Path,
    import_evidence_path: Path,
    e2e_evidence_path: Path,
    provider_evidence_path: Path,
    observability_path: Path,
) -> dict[str, Any]:
    return evaluate_e1(
        candidate=load_yaml(candidate_path),
        manifest=load_yaml(manifest_path),
        runtime_evidence=load_yaml(runtime_evidence_path),
        import_evidence=load_yaml(import_evidence_path),
        e2e_evidence=load_yaml(e2e_evidence_path),
        provider_evidence=load_yaml(provider_evidence_path),
        observability=load_yaml(observability_path),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Phase E1 staging evidence")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--import-evidence", type=Path, required=True)
    parser.add_argument("--e2e-evidence", type=Path, required=True)
    parser.add_argument("--provider-evidence", type=Path, required=True)
    parser.add_argument("--observability", type=Path, required=True)
    parser.add_argument("--write-staging-validation", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate_paths(
            candidate_path=args.candidate,
            manifest_path=args.manifest,
            runtime_evidence_path=args.runtime_evidence,
            import_evidence_path=args.import_evidence,
            e2e_evidence_path=args.e2e_evidence,
            provider_evidence_path=args.provider_evidence,
            observability_path=args.observability,
        )
        if args.write_staging_validation:
            args.write_staging_validation.parent.mkdir(parents=True, exist_ok=True)
            args.write_staging_validation.write_text(
                yaml.safe_dump(result["staging_validation"], sort_keys=False),
                encoding="utf-8",
            )
        print(yaml.safe_dump(result, sort_keys=False))
        return 0 if result["status"] == "passed" else 2
    except E1Error as exc:
        print(f"e1-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
