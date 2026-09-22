from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]


class ProductionReadinessError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProductionReadinessError(f"Missing readiness input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProductionReadinessError(f"Expected mapping in {path}")
    return value


def _check(check_id: str, details: list[str]) -> dict[str, Any]:
    return {"id": check_id, "status": "fail" if details else "pass", "details": details}


def evaluate_readiness(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    plan_path = project / "production" / "production-plan.yaml"
    plan = load_yaml(plan_path)
    errors = validate_document(plan, "production-plan")
    if errors:
        raise ProductionReadinessError("Invalid production plan: " + "; ".join(errors))

    checks: list[dict[str, Any]] = []

    checks.append(_check(
        "approved-scope-resolved",
        list(plan.get("blocking_items", [])),
    ))
    checks.append(_check(
        "capability-ownership",
        [
            item["id"] for item in plan["capabilities"]
            if item.get("owner") == "unmapped" or item.get("disposition") == "blocked"
        ],
    ))
    checks.append(_check(
        "runtime-provider-mapping",
        [
            item["domain"] for item in plan["runtimes"]
            if item.get("status") == "blocked" or not item.get("provider")
        ],
    ))
    checks.append(_check(
        "runtime-version-pinning",
        [
            f"{item['domain']}:{item['provider']}"
            for item in plan["runtimes"]
            if item.get("required") and not item.get("version")
        ],
    ))
    checks.append(_check(
        "surface-production-mapping",
        [
            item["surface"] for item in plan["surfaces"]
            if item.get("status") != "mapped"
        ],
    ))
    checks.append(_check(
        "integration-provider-selection",
        [
            item["integration_id"] for item in plan["integrations"]
            if item.get("selection_status") != "resolved" or item.get("status") != "mapped"
        ],
    ))
    checks.append(_check(
        "credential-inventory",
        [
            item["integration_id"] for item in plan["integrations"]
            if item.get("production_mode") == "live" and not item.get("credential_refs")
        ],
    ))
    checks.append(_check(
        "data-ownership",
        [] if plan["data"].get("entity_ownership") else ["no canonical entities"],
    ))
    checks.append(_check(
        "migration-strategy",
        [
            key for key in (
                "demo_data_action", "master_data_action",
                "opening_inventory_action", "opening_finance_action"
            )
            if not plan["data"].get(key)
        ],
    ))
    deferred = set(plan["configuration"].get("deferred_capabilities", []))
    included = {item["id"] for item in plan["capabilities"]}
    checks.append(_check(
        "deferred-scope-exclusion",
        sorted(deferred & included),
    ))
    checks.append(_check(
        "production-test-plan",
        [] if plan["acceptance"].get("required_checks") else ["no required production checks"],
    ))

    blockers = [
        f"{item['id']}: {', '.join(item['details'])}"
        for item in checks if item["status"] == "fail"
    ]
    result = {
        "readiness_id": f"PRODREADY-{client_id}-v{plan['scope']['version']}",
        "client_id": client_id,
        "production_plan_ref": "production/production-plan.yaml",
        "checks": checks,
        "blocking_items": blockers,
        "status": "blocked" if blockers else "production-ready",
    }
    errors = validate_document(result, "production-readiness")
    if errors:
        raise ProductionReadinessError("Generated production readiness invalid: " + "; ".join(errors))
    return result


def write_readiness(client_id: str, root: Path = ROOT) -> Path:
    result = evaluate_readiness(client_id, root)
    path = root / "client-projects" / client_id / "production" / "production-readiness.yaml"
    path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Phase-D1 production readiness")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        result = evaluate_readiness(args.client, args.root)
        if args.write:
            path = write_readiness(args.client, args.root)
            print(path.relative_to(args.root))
        print(yaml.safe_dump(result, sort_keys=False))
        return 0 if result["status"] == "production-ready" else 2
    except ProductionReadinessError as exc:
        print(f"production-readiness-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
