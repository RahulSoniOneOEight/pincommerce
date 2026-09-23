from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.staging.e1 import evaluate_e1, load_yaml
from tooling.staging.provider_probe import collect as collect_provider_evidence


class StagingExecutionError(RuntimeError):
    pass


def _json_env(name: str) -> dict[str, Any]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StagingExecutionError(f"{name} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise StagingExecutionError(f"{name} must contain a JSON object")
    return value


def _probe_http(url: str, *, timeout: int = 15, attempts: int = 3) -> tuple[str, str]:
    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                code = int(response.status)
                body = response.read(512).decode("utf-8", errors="replace")
                if 200 <= code < 400:
                    return "pass", f"HTTP {code}: {body[:180]}"
                last_error = f"HTTP {code}: {body[:180]}"
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = str(exc)
        if attempt < attempts:
            time.sleep(2)
    return "fail", last_error or "probe failed"


def _status(rows: list[dict[str, Any]], field: str = "status") -> str:
    values = [row.get(field) for row in rows]
    if any(value == "fail" for value in values):
        return "failed"
    if any(value == "not-run" for value in values):
        return "blocked"
    return "passed"


def collect_runtime_evidence(candidate_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    endpoints = _json_env("STAGING_RUNTIME_ENDPOINTS_JSON")
    attestations = _json_env("STAGING_RUNTIME_ATTESTATIONS_JSON")
    rows: list[dict[str, Any]] = []
    for runtime in manifest.get("runtimes", []):
        if not runtime.get("required"):
            continue
        runtime_id = str(runtime["id"])
        endpoint = str(endpoints.get(runtime_id, "") or "").strip()
        if endpoint:
            status, evidence = _probe_http(endpoint)
        else:
            attestation = attestations.get(runtime_id)
            if isinstance(attestation, dict) and attestation.get("status") == "pass":
                status = "pass"
                evidence = str(attestation.get("evidence") or "environment attestation")
            else:
                status = "not-run"
                evidence = f"missing runtime endpoint/attestation for {runtime_id}"
        rows.append({"id": runtime_id, "status": status, "evidence": evidence})
    result = {"candidate_id": candidate_id, "runtimes": rows, "status": _status(rows)}
    errors = validate_document(result, "staging-runtime-evidence")
    if errors:
        raise StagingExecutionError("Invalid runtime evidence: " + "; ".join(errors))
    return result


def collect_import_evidence(candidate_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    probes = _json_env("STAGING_IMPORT_PROBES_JSON")
    rows: list[dict[str, Any]] = []
    for item in manifest.get("data_imports", []):
        if not item.get("required"):
            continue
        import_id = str(item["id"])
        endpoint = str(probes.get(import_id, "") or "").strip()
        if not endpoint:
            rows.append({
                "id": import_id,
                "status": "not-run",
                "readback_status": "not-run",
                "evidence": f"missing import/readback probe for {import_id}",
            })
            continue
        status, evidence = _probe_http(endpoint)
        rows.append({
            "id": import_id,
            "status": status,
            "readback_status": status,
            "evidence": evidence,
        })
    result = {"candidate_id": candidate_id, "imports": rows, "status": _status(rows)}
    errors = validate_document(result, "staging-import-evidence")
    if errors:
        raise StagingExecutionError("Invalid import evidence: " + "; ".join(errors))
    return result


def collect_e2e_evidence(candidate_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    probes = _json_env("STAGING_E2E_PROBES_JSON")
    rows: list[dict[str, Any]] = []
    for flow in manifest.get("e2e_flows", []):
        flow_id = str(flow)
        endpoint = str(probes.get(flow_id, "") or "").strip()
        if not endpoint:
            rows.append({"id": flow_id, "status": "not-run", "evidence": f"missing E2E probe for {flow_id}"})
            continue
        status, evidence = _probe_http(endpoint)
        rows.append({"id": flow_id, "status": status, "evidence": evidence})
    result = {"candidate_id": candidate_id, "flows": rows, "status": _status(rows)}
    errors = validate_document(result, "staging-e2e-evidence")
    if errors:
        raise StagingExecutionError("Invalid E2E evidence: " + "; ".join(errors))
    return result


def collect_observability_evidence(candidate_id: str) -> dict[str, Any]:
    probes = _json_env("STAGING_OBSERVABILITY_PROBES_JSON")
    rows = []
    for kind in ("metric", "trace", "error", "alert"):
        endpoint = str(probes.get(kind, "") or "").strip()
        if not endpoint:
            rows.append({
                "kind": kind,
                "name": f"staging.{kind}",
                "status": "not-run",
                "evidence": f"missing observability probe for {kind}",
            })
            continue
        status, evidence = _probe_http(endpoint)
        rows.append({
            "kind": kind,
            "name": f"staging.{kind}",
            "status": status,
            "evidence": evidence,
        })
    if any(row["status"] == "fail" for row in rows):
        overall = "failed"
    elif any(row["status"] == "not-run" for row in rows):
        overall = "draft"
    else:
        overall = "passed"
    result = {
        "evidence_id": f"OBS-{candidate_id}",
        "candidate_id": candidate_id,
        "signals": rows,
        "status": overall,
    }
    errors = validate_document(result, "observability-evidence")
    if errors:
        raise StagingExecutionError("Invalid observability evidence: " + "; ".join(errors))
    return result


def execute(
    *,
    candidate_path: Path,
    manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    candidate = load_yaml(candidate_path)
    manifest = load_yaml(manifest_path)
    candidate_id = str(candidate["candidate_id"])
    if manifest.get("candidate_id") != candidate_id:
        raise StagingExecutionError("manifest does not reference exact candidate")

    runtime = collect_runtime_evidence(candidate_id, manifest)
    imports = collect_import_evidence(candidate_id, manifest)
    e2e = collect_e2e_evidence(candidate_id, manifest)
    providers = collect_provider_evidence(candidate_id)
    observability = collect_observability_evidence(candidate_id)

    result = evaluate_e1(
        candidate=candidate,
        manifest=manifest,
        runtime_evidence=runtime,
        import_evidence=imports,
        e2e_evidence=e2e,
        provider_evidence=providers,
        observability=observability,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    documents = {
        "runtime-evidence.yaml": runtime,
        "import-evidence.yaml": imports,
        "e2e-evidence.yaml": e2e,
        "provider-evidence.yaml": providers,
        "observability.yaml": observability,
        "staging-validation.yaml": result["staging_validation"],
    }
    for name, value in documents.items():
        (output_dir / name).write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute exact-candidate staging evidence collection")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = execute(candidate_path=args.candidate, manifest_path=args.manifest, output_dir=args.output_dir)
        print(yaml.safe_dump(result, sort_keys=False))
        return 0 if result["status"] == "passed" else 2
    except StagingExecutionError as exc:
        print(f"staging-execution-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
