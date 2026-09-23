from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.release.candidate import create_candidate

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CANDIDATE_ARTIFACTS = (
    "production/production-plan.yaml",
    "production/production-readiness.yaml",
    "production/production-execution.yaml",
    "production/phase-d-completion.yaml",
    "qa/cross-domain.yaml",
    "qa/production-qa.yaml",
)


class StagingManifestError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise StagingManifestError(f"Missing staging manifest source: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StagingManifestError(f"Expected mapping in {path}")
    return value


def build_candidate_and_manifest(
    client_id: str,
    source_revision: str,
    *,
    created_by: str,
    root: Path = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project = root / "client-projects" / client_id
    artifact_paths = [
        Path("client-projects") / client_id / relative
        for relative in DEFAULT_CANDIDATE_ARTIFACTS
    ]
    candidate = create_candidate(
        client_id=client_id,
        source_revision=source_revision,
        artifact_paths=artifact_paths,
        created_by=created_by,
        root=root,
    )

    plan = load_yaml(project / "production" / "production-plan.yaml")
    readiness = load_yaml(project / "production" / "production-readiness.yaml")
    if readiness.get("status") != "production-ready" or readiness.get("blocking_items"):
        raise StagingManifestError("Phase D production readiness is not production-ready")

    runtimes = []
    for runtime in plan.get("runtimes", []):
        if not runtime.get("required"):
            continue
        version = runtime.get("version")
        if not version:
            raise StagingManifestError(f"Runtime version missing: {runtime.get('domain')}")
        healthcheck = {
            "commerce": "/health",
            "marketplace": "/health",
            "erp": "/",
            "search": "/health",
            "database": "pg_isready",
            "support": "adapter-or-service-health",
            "automation": "adapter-or-service-health",
            "experience_mobile": "build-and-smoke",
            "experience_web": "build-and-smoke",
        }.get(runtime["domain"], "service-health")
        runtimes.append({
            "id": runtime["domain"],
            "provider": runtime["provider"],
            "version": version,
            "required": True,
            "healthcheck": healthcheck,
        })

    imports = [
        {
            "id": "master-data",
            "target": "canonical-production-owners",
            "required": True,
            "readback": "identity-and-count-reconciliation",
        },
        {
            "id": "opening-inventory",
            "target": "erp",
            "required": True,
            "readback": "warehouse-sku-reconciliation",
        },
        {
            "id": "opening-finance",
            "target": "erp",
            "required": True,
            "readback": "trial-balance-ar-ap-reconciliation",
        },
    ]
    if any(item.get("provider") == "mercur" for item in runtimes):
        imports.extend([
            {
                "id": "marketplace-sellers-offers",
                "target": "marketplace",
                "required": True,
                "readback": "seller-offer-reconciliation",
            },
            {
                "id": "opening-seller-settlements",
                "target": "marketplace-and-erp",
                "required": True,
                "readback": "settlement-payable-reconciliation",
            },
        ])

    provider_checks = [
        item["selected_provider"]
        for item in plan.get("integrations", [])
        if item.get("production_mode") == "live" and item.get("selected_provider")
    ]

    cross_domain = load_yaml(project / "qa" / "cross-domain.yaml")
    e2e_flows = [
        item["journey"] for item in cross_domain.get("cases", [])
        if item.get("status") == "pass"
    ]
    if not e2e_flows:
        raise StagingManifestError("No passing Phase-D cross-domain journeys available")

    manifest = {
        "manifest_id": f"STGMAN-{client_id}-{source_revision[:12]}",
        "client_id": client_id,
        "candidate_id": candidate["candidate_id"],
        "candidate_digest": candidate["artifact_digest"],
        "source_revision": source_revision,
        "runtimes": runtimes,
        "data_imports": imports,
        "e2e_flows": e2e_flows,
        "provider_checks": provider_checks,
        "status": "planned",
    }
    errors = validate_document(manifest, "staging-manifest")
    if errors:
        raise StagingManifestError("Generated staging manifest invalid: " + "; ".join(errors))
    return candidate, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build exact-candidate Phase E1 staging manifest")
    parser.add_argument("--client", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--created-by", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        candidate, manifest = build_candidate_and_manifest(
            args.client,
            args.source_revision,
            created_by=args.created_by,
            root=args.root,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        candidate_path = args.output_dir / f"{candidate['candidate_id']}.yaml"
        manifest_path = args.output_dir / "staging-manifest.yaml"
        candidate_path.write_text(yaml.safe_dump(candidate, sort_keys=False), encoding="utf-8")
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        print(candidate_path)
        print(manifest_path)
        return 0
    except StagingManifestError as exc:
        print(f"staging-manifest-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
