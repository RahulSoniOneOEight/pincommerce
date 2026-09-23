from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]

CAPABILITY_OWNERS = {
    "authentication": "experience",
    "audit": "ops",
    "catalogue": "commerce",
    "search": "search",
    "pricing": "commerce",
    "promotions": "commerce",
    "cart": "commerce",
    "checkout": "commerce",
    "orders": "commerce",
    "inventory-availability": "erp",
    "fulfilment": "commerce",
    "return-refund": "commerce",
    "analytics": "analytics",
    "b2b-account": "commerce",
    "quote-rfq": "commerce",
    "loyalty": "commerce",
    "customer-support": "support",
    "lifecycle-automation": "automation",
    "ops-exceptions": "ops",
    "credit-management": "commerce",
    "approval-workflow": "commerce",
    "reorder": "commerce",
}

PROVIDER_ADAPTERS = {
    "medusa": "platform/commerce/medusa/adapter.yaml",
    "mercur": "platform/marketplace/mercur/adapter.yaml",
    "tryton": "platform/erp/tryton/adapter.yaml",
    "meilisearch": "platform/search/meilisearch/adapter.yaml",
    "chatwoot": "platform/customer/chatwoot/adapter.yaml",
    "activepieces": "platform/automation/activepieces/adapter.yaml",
    "razorpay": "connectors/payments/razorpay/adapter.yaml",
    "cashfree": "connectors/payments/cashfree/adapter.yaml",
    "shiprocket": "connectors/logistics/shiprocket/adapter.yaml",
    "delhivery": "connectors/logistics/delhivery/adapter.yaml",
    "meta-whatsapp-cloud": "connectors/messaging/whatsapp/adapter.yaml",
    "meta-whatsapp-cloud-api": "connectors/messaging/whatsapp/adapter.yaml",
}

PROVIDER_BASELINES = {
    "medusa": "platform/prototype/baselines/medusa-standard-v1.yaml",
    "mercur": "platform/prototype/baselines/mercur-standard-v1.yaml",
    "tryton": "platform/prototype/baselines/tryton-standard-v1.yaml",
}

SURFACE_PROVIDER_KEYS = {
    "customer-app": "experience_mobile",
    "web-store": "experience_web",
    "commerce-admin": "commerce",
    "seller-portal": "marketplace",
    "erp": "erp",
    "analytics": "experience_web",
    "warehouse": "erp",
    "customer-support": "support",
    "ops-console": "experience_web",
}

ACCEPTANCE_CHECKS = [
    "approved-scope-resolved",
    "capability-ownership",
    "runtime-provider-mapping",
    "runtime-version-pinning",
    "surface-production-mapping",
    "integration-provider-selection",
    "credential-inventory",
    "data-ownership",
    "migration-strategy",
    "deferred-scope-exclusion",
    "production-test-plan",
]


class ProductionCompileError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ProductionCompileError(f"Missing production compiler input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProductionCompileError(f"Expected mapping in {path}")
    return value


def save_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _production_selections(project: Path) -> tuple[dict[str, str], dict[str, str]]:
    path = project / "production" / "provider-selections.yaml"
    if not path.exists():
        return {}, {}
    value = load_yaml(path)
    errors = validate_document(value, "production-provider-selections")
    if errors:
        raise ProductionCompileError(
            "Invalid production/provider-selections.yaml: " + "; ".join(errors)
        )
    integrations = value.get("integrations", {})
    runtime_versions = value.get("runtime_versions", {})
    return (
        {str(k): str(v) for k, v in integrations.items()},
        {str(k): str(v) for k, v in runtime_versions.items()},
    )


def _approved_overlays(project: Path, baseline: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for ref in baseline.get("architecture_decisions", []):
        refs.append(ref)
    changes_dir = project / "changes"
    if changes_dir.exists():
        for path in sorted(changes_dir.glob("CHG-*.yaml")):
            value = load_yaml(path)
            if value.get("status") in {"approved", "implemented", "closed"}:
                refs.append(f"changes/{path.name}")
    return list(dict.fromkeys(refs))


def build_production_plan(client_id: str, root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    project = root / "client-projects" / client_id
    current = load_yaml(project / "approved" / "current-scope.yaml")
    current_errors = validate_document(current, "current-scope")
    if current_errors:
        raise ProductionCompileError("Invalid current scope: " + "; ".join(current_errors))

    baseline = load_yaml(project / current["baseline_ref"])
    baseline_errors = validate_document(baseline, "scope-baseline")
    if baseline_errors:
        raise ProductionCompileError("Invalid approved scope baseline: " + "; ".join(baseline_errors))
    if baseline.get("baseline_id") != current.get("baseline_id"):
        raise ProductionCompileError("Current scope pointer and immutable baseline disagree")

    solution_ref = baseline.get("solution_ref", "solution/solution-contract.yaml")
    solution = load_yaml(project / solution_ref)
    surface_map = load_yaml(project / "derived" / "surface-map.yaml")
    integration_map = load_yaml(project / "derived" / "integration-map.yaml")
    data_contract = load_yaml(project / "contracts" / "data-contract.yaml")
    business_contract = load_yaml(project / "contracts" / "business-contract.yaml")
    selections, runtime_versions = _production_selections(project)
    overlays = _approved_overlays(project, baseline)

    blockers: list[str] = []
    capability_rows: list[dict[str, Any]] = []
    for capability in baseline.get("included_capabilities", []):
        owner = CAPABILITY_OWNERS.get(capability)
        disposition = "standard"
        notes: list[str] = []
        if not owner:
            owner = "unmapped"
            disposition = "blocked"
            blocker = f"approved capability has no production owner: {capability}"
            blockers.append(blocker)
            notes.append(blocker)
        capability_rows.append({
            "id": capability,
            "owner": owner,
            "disposition": disposition,
            "source": current["baseline_ref"],
            "notes": notes,
        })

    providers = solution.get("providers", {})
    runtime_rows: list[dict[str, Any]] = []
    for domain_key, value in providers.items():
        provider = value.get("provider")
        if not provider:
            blockers.append(f"solution runtime has no provider: {domain_key}")
            continue
        adapter_ref = PROVIDER_ADAPTERS.get(provider)
        baseline_ref = PROVIDER_BASELINES.get(provider)
        status = "mapped"
        if provider in PROVIDER_ADAPTERS and not (root / PROVIDER_ADAPTERS[provider]).exists():
            status = "blocked"
            blockers.append(f"provider adapter missing: {provider}")
        runtime_rows.append({
            "domain": domain_key,
            "provider": provider,
            "required": True,
            "production_mode": "real",
            "adapter_ref": adapter_ref,
            "baseline_ref": baseline_ref,
            "version": runtime_versions.get(domain_key) or value.get("version"),
            "overlays": list(value.get("extensions", [])),
            "status": status,
        })

    surface_rows: list[dict[str, Any]] = []
    for surface in surface_map.get("required", []):
        provider_key = SURFACE_PROVIDER_KEYS.get(surface)
        provider = providers.get(provider_key, {}).get("provider") if provider_key else None
        status = "mapped" if provider else "blocked"
        if status == "blocked":
            blockers.append(f"required surface has no production runtime mapping: {surface}")
        surface_rows.append({
            "surface": surface,
            "provider": provider,
            "production_target": provider_key or "unmapped",
            "status": status,
        })

    integration_rows: list[dict[str, Any]] = []
    for item in integration_map.get("integrations", []):
        integration_id = item["id"]
        candidates = list(item.get("provider_candidates", []))
        selected = selections.get(integration_id)
        if selected and selected not in candidates:
            blockers.append(
                f"selected provider {selected} is not an approved candidate for {integration_id}"
            )
            selected = None
        if not selected and len(candidates) == 1:
            selected = candidates[0]
        selection_status = "resolved" if selected else "selection-required"
        if not selected:
            blockers.append(
                f"production provider selection required for integration: {integration_id}"
            )
        adapter_ref = PROVIDER_ADAPTERS.get(selected) if selected else None
        if selected and not adapter_ref:
            blockers.append(f"production adapter missing for integration provider: {selected}")
        reconciliation_required = (
            item.get("domain") == "payments" or item.get("criticality") == "critical"
        )
        integration_rows.append({
            "integration_id": integration_id,
            "domain": item.get("domain", integration_id),
            "provider_candidates": candidates,
            "selected_provider": selected,
            "selection_status": selection_status,
            "production_mode": "live" if selected else "unresolved",
            "credential_refs": list(item.get("credential_refs", [])),
            "adapter_ref": adapter_ref,
            "reconciliation_required": reconciliation_required,
            "status": "mapped" if selected and adapter_ref else "blocked",
        })

    entity_ownership = [
        {
            "entity": item["name"],
            "owner": item["canonical_owner"],
            "consumers": list(item.get("consumers", [])),
        }
        for item in data_contract.get("entities", [])
    ]
    if not entity_ownership:
        blockers.append("data contract has no canonical entity ownership")

    version = int(current["version"])
    plan = {
        "production_plan_id": f"PRODPLAN-{client_id}-v{version}",
        "client_id": client_id,
        "scope": {
            "current_scope_ref": "approved/current-scope.yaml",
            "baseline_ref": current["baseline_ref"],
            "baseline_id": current["baseline_id"],
            "version": version,
        },
        "source": {
            "solution_ref": solution_ref,
            "business_contract_ref": "contracts/business-contract.yaml",
            "data_contract_ref": "contracts/data-contract.yaml",
            "prototype_revision_ref": baseline.get("prototype_revision_ref"),
            "review_round_ref": baseline.get("review_round_ref"),
            "architecture_decision_refs": list(baseline.get("architecture_decisions", [])),
        },
        "capabilities": capability_rows,
        "surfaces": surface_rows,
        "runtimes": runtime_rows,
        "integrations": integration_rows,
        "data": {
            "demo_data_action": "replace",
            "master_data_action": "migrate",
            "opening_inventory_action": "load",
            "opening_finance_action": "load",
            "entity_ownership": entity_ownership,
        },
        "configuration": {
            "strategy": "standard-baseline-plus-approved-overlays",
            "approved_overlays": overlays,
            "deferred_capabilities": list(baseline.get("deferred_capabilities", [])),
            "excluded_capabilities": list(baseline.get("excluded_capabilities", [])),
        },
        "acceptance": {"required_checks": ACCEPTANCE_CHECKS},
        "blocking_items": list(dict.fromkeys(blockers)),
        "status": "blocked" if blockers else "draft",
    }

    migration = {
        "migration_plan_id": f"MIGPLAN-{client_id}-v{version}",
        "client_id": client_id,
        "source_scope_ref": current["baseline_ref"],
        "steps": [
            {
                "id": "replace-demo-data",
                "dataset": "prototype-demo-dataset",
                "action": "replace-demo",
                "target": "all-production-runtimes",
                "verification": "no demo-only identities remain in production data",
            },
            {
                "id": "migrate-master-data",
                "dataset": "customers-products-parties",
                "action": "migrate",
                "target": "canonical owners from data contract",
                "verification": "record counts and identity mapping reconcile",
            },
            {
                "id": "load-opening-inventory",
                "dataset": "opening-inventory",
                "action": "load",
                "target": "erp",
                "verification": "warehouse/SKU quantities reconcile to approved opening snapshot",
            },
            {
                "id": "load-opening-finance",
                "dataset": "opening-finance",
                "action": "load",
                "target": "erp",
                "verification": "trial balance and AR/AP opening balances reconcile",
            },
        ],
        "blocking_items": [],
        "status": "ready",
    }

    runtimes_doc = {
        "client_id": client_id,
        "production_plan_ref": "production/production-plan.yaml",
        "runtimes": runtime_rows,
    }
    integrations_doc = {
        "client_id": client_id,
        "production_plan_ref": "production/production-plan.yaml",
        "integrations": integration_rows,
    }
    configuration_doc = {
        "client_id": client_id,
        "production_plan_ref": "production/production-plan.yaml",
        "strategy": plan["configuration"]["strategy"],
        "approved_overlays": overlays,
        "deferred_capabilities": plan["configuration"]["deferred_capabilities"],
        "excluded_capabilities": plan["configuration"]["excluded_capabilities"],
    }

    for contract, value in (
        ("production-plan", plan),
        ("production-migration-plan", migration),
    ):
        errors = validate_document(value, contract)
        if errors:
            raise ProductionCompileError(f"Generated {contract} invalid: " + "; ".join(errors))

    _ = business_contract
    return plan, runtimes_doc, integrations_doc, configuration_doc, migration


def write_production_plan(client_id: str, root: Path = ROOT) -> list[Path]:
    plan, runtimes, integrations, configuration, migration = build_production_plan(client_id, root)
    base = root / "client-projects" / client_id / "production"
    outputs = [
        (base / "production-plan.yaml", plan),
        (base / "runtimes.yaml", runtimes),
        (base / "integrations.yaml", integrations),
        (base / "configuration.yaml", configuration),
        (base / "data-migration.yaml", migration),
        (base / "acceptance.yaml", {
            "client_id": client_id,
            "production_plan_ref": "production/production-plan.yaml",
            "required_checks": plan["acceptance"]["required_checks"],
        }),
    ]
    for path, value in outputs:
        save_yaml(path, value)
    return [path for path, _ in outputs]


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile approved scope into production plan")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()
    try:
        plan, *_ = build_production_plan(args.client, args.root)
        if args.print_only:
            print(yaml.safe_dump(plan, sort_keys=False))
        else:
            for path in write_production_plan(args.client, args.root):
                print(path.relative_to(args.root))
        return 0
    except ProductionCompileError as exc:
        print(f"production-compile-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
