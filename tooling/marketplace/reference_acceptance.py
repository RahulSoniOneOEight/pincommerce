from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.onboarding.engine import build_blueprint
from tooling.production.compiler import (
    CAPABILITY_OWNERS,
    PROVIDER_ADAPTERS,
    SURFACE_PROVIDER_KEYS,
    build_migration_steps,
)
from tooling.prototype.core_runtime import build_core_runtime
from tooling.prototype.demo_data import build_demo_dataset
from tooling.prototype.seed_bundle import build_seed_bundle

ROOT = Path(__file__).resolve().parents[2]


class MarketplaceAcceptanceError(RuntimeError):
    pass


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def evaluate_reference_marketplace(root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / "reference-marketplace"
    input_path = project / "input" / "client-input.yaml"
    if not input_path.exists():
        raise MarketplaceAcceptanceError(f"missing marketplace input: {input_path}")

    client_input = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    errors = validate_document(client_input, "client-input")
    if errors:
        raise MarketplaceAcceptanceError("invalid marketplace client input: " + "; ".join(errors))

    blueprint = build_blueprint("reference-marketplace", root)
    files = blueprint.files

    classification = files["derived/classification-evidence.yaml"]
    benchmark = files["derived/benchmark-report.yaml"]
    entities = files["derived/entity-map.yaml"]["entities"]
    dependencies = {
        item["id"] for item in files["derived/dependency-map.yaml"]["critical_cross_domain_flows"]
    }
    solution = files["solution/solution-contract.yaml"]

    a_issues: list[str] = []
    if "marketplace" not in classification.get("archetypes", []):
        a_issues.append("marketplace archetype not activated")
    truth = files["derived/truth-register.yaml"]
    if not any(item.get("path") == "marketplace_requirements" for item in truth.get("records", [])):
        a_issues.append("marketplace requirements absent from truth register")
    expected = benchmark.get("expected", {})
    for capability in ("seller-onboarding", "commissions", "settlements"):
        if capability not in expected.get("core_capabilities", []):
            a_issues.append(f"missing marketplace benchmark capability: {capability}")

    b_issues: list[str] = []
    marketplace_provider = solution.get("providers", {}).get("marketplace", {})
    if marketplace_provider.get("provider") != "mercur":
        b_issues.append("Mercur not selected for marketplace")
    for entity in ("seller", "seller-offer", "marketplace-order-allocation", "commission", "seller-settlement"):
        if entity not in entities:
            b_issues.append(f"missing marketplace entity: {entity}")
    for flow in (
        "seller-onboarding-to-approval",
        "commerce-order-to-seller-allocation",
        "seller-settlement-to-accounting",
    ):
        if flow not in dependencies:
            b_issues.append(f"missing marketplace dependency flow: {flow}")

    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        temp_project = temp_root / "client-projects" / "reference-marketplace"
        _write_yaml(temp_project / "input" / "client-input.yaml", client_input)
        _write_yaml(temp_project / "solution" / "solution-contract.yaml", solution)
        runtime = build_core_runtime("reference-marketplace", temp_root)

    c_issues: list[str] = []
    modules = {item["provider"]: item for item in runtime["modules"]}
    mercur = modules.get("mercur", {})
    if not mercur.get("required") or mercur.get("mode") != "real-core":
        c_issues.append("Mercur is not a required real-core runtime")

    dataset = build_demo_dataset("reference-marketplace")
    seed = build_seed_bundle(dataset)["mercur"]
    for key in (
        "sellers",
        "seller_offers",
        "marketplace_allocations",
        "commission_ledger",
        "seller_settlements",
        "seller_payout_reconciliations",
    ):
        if not seed.get(key):
            c_issues.append(f"Mercur seed missing {key}")

    d_issues: list[str] = []
    for capability in (
        "seller-onboarding",
        "seller-catalogue",
        "seller-inventory",
        "marketplace-orders",
        "commissions",
        "settlements",
        "payout-reconciliation",
    ):
        if CAPABILITY_OWNERS.get(capability) != "marketplace":
            d_issues.append(f"production owner is not marketplace: {capability}")
    if SURFACE_PROVIDER_KEYS.get("seller-portal") != "marketplace":
        d_issues.append("seller portal not mapped to marketplace runtime")
    if PROVIDER_ADAPTERS.get("mercur") != "platform/marketplace/mercur/adapter.yaml":
        d_issues.append("Mercur production adapter missing")
    migration_ids = {item["id"] for item in build_migration_steps(True)}
    for migration_id in ("migrate-marketplace-sellers", "load-opening-seller-settlements"):
        if migration_id not in migration_ids:
            d_issues.append(f"missing marketplace migration step: {migration_id}")

    checks = {
        "A-client-intelligence": a_issues,
        "B-solution-intelligence": b_issues,
        "C-functional-marketplace-prototype": c_issues,
        "D-productionization": d_issues,
    }
    blockers = [
        f"{stage}: {issue}"
        for stage, issues in checks.items()
        for issue in issues
    ]
    return {
        "client_id": "reference-marketplace",
        "checks": {
            stage: "pass" if not issues else "fail"
            for stage, issues in checks.items()
        },
        "blocking_items": blockers,
        "status": "complete" if not blockers else "blocked",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reference marketplace A-D acceptance")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = evaluate_reference_marketplace(args.root)
        print(yaml.safe_dump(result, sort_keys=False))
        return 0 if result["status"] == "complete" else 2
    except MarketplaceAcceptanceError as exc:
        print(f"marketplace-acceptance-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
