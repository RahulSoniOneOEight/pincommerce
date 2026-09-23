from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.production.compiler import build_production_plan
from tooling.production.readiness import evaluate_readiness

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_D_CHECKS = {
    "d1-production-plan",
    "d2-runtime-provisioning-contract",
    "d3-provider-bindings",
    "d4-migration-readiness",
    "d5-cross-domain-integration",
    "d6-production-qa",
}


class PhaseDCompletionError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PhaseDCompletionError(f"Missing Phase-D artifact: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PhaseDCompletionError(f"Expected mapping in {path}")
    return value


def _fail(checks: list[dict[str, Any]], check_id: str, details: list[str]) -> None:
    checks.append({"id": check_id, "status": "fail" if details else "pass", "details": details})


def evaluate_documents(
    plan: dict[str, Any],
    readiness: dict[str, Any],
    execution: dict[str, Any],
    cross_domain: dict[str, Any],
    production_qa: dict[str, Any],
    completion: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    _fail(
        checks,
        "d1-production-plan",
        [] if readiness.get("status") == "production-ready" and not readiness.get("blocking_items") else ["production readiness is not production-ready"],
    )

    plan_runtimes = {item["domain"]: item for item in plan.get("runtimes", [])}
    execution_runtimes = {item["domain"]: item for item in execution.get("runtimes", [])}
    runtime_issues: list[str] = []
    for domain, expected in plan_runtimes.items():
        actual = execution_runtimes.get(domain)
        if not actual:
            runtime_issues.append(f"missing runtime execution: {domain}")
            continue
        if actual.get("provider") != expected.get("provider"):
            runtime_issues.append(f"provider mismatch for {domain}")
        if actual.get("version") != expected.get("version"):
            runtime_issues.append(f"version mismatch for {domain}")
        version = str(actual.get("version", ""))
        if not version or "<" in version or "acceptance-" in version:
            runtime_issues.append(f"non-production version pin for {domain}")
        if actual.get("status") != "validated":
            runtime_issues.append(f"runtime not validated: {domain}")
    _fail(checks, "d2-runtime-provisioning-contract", runtime_issues)

    plan_integrations = {item["integration_id"]: item for item in plan.get("integrations", [])}
    bindings = {item["integration_id"]: item for item in execution.get("provider_bindings", [])}
    binding_issues: list[str] = []
    for integration_id, expected in plan_integrations.items():
        actual = bindings.get(integration_id)
        if not actual:
            binding_issues.append(f"missing provider binding: {integration_id}")
            continue
        if actual.get("provider") != expected.get("selected_provider"):
            binding_issues.append(f"provider mismatch: {integration_id}")
        if actual.get("adapter_ref") != expected.get("adapter_ref"):
            binding_issues.append(f"adapter mismatch: {integration_id}")
        if not actual.get("credential_refs"):
            binding_issues.append(f"credential inventory missing: {integration_id}")
        if actual.get("status") != "configured":
            binding_issues.append(f"binding not configured: {integration_id}")
        if actual.get("verification") == "contract-tested" and actual.get("staging_live_verification") is not True:
            binding_issues.append(f"live verification not delegated to staging: {integration_id}")
    _fail(checks, "d3-provider-bindings", binding_issues)

    migration = execution.get("migration", {})
    migration_issues = []
    for key in (
        "demo_data_replaced",
        "master_data_strategy_validated",
        "opening_inventory_strategy_validated",
        "opening_finance_strategy_validated",
    ):
        if migration.get(key) is not True:
            migration_issues.append(key)
    if migration.get("status") != "validated":
        migration_issues.append("migration status")
    _fail(checks, "d4-migration-readiness", migration_issues)

    integration = execution.get("integration", {})
    integration_issues = []
    for key in ("idempotency", "retry", "dead_letter", "reconciliation"):
        if integration.get(key) is not True:
            integration_issues.append(key)
    if integration.get("status") != "validated":
        integration_issues.append("integration status")
    failed_cases = [
        item.get("id", "unknown")
        for item in cross_domain.get("cases", [])
        if item.get("status") != "pass"
    ]
    integration_issues.extend(failed_cases)
    if cross_domain.get("status") != "passed" or cross_domain.get("blocking_items"):
        integration_issues.append("cross-domain QA")
    _fail(checks, "d5-cross-domain-integration", integration_issues)

    qa_issues = [
        str(key)
        for key, value in (production_qa.get("checks") or {}).items()
        if value != "pass"
    ]
    if production_qa.get("status") != "passed" or production_qa.get("blocking_items"):
        qa_issues.append("production QA")
    _fail(checks, "d6-production-qa", qa_issues)

    completion_checks = {
        item.get("id"): item.get("status")
        for item in completion.get("checks", [])
    }
    missing_completion = sorted(REQUIRED_D_CHECKS - set(completion_checks))
    if missing_completion:
        checks.append({
            "id": "phase-d-completion-record",
            "status": "fail",
            "details": [f"missing completion checks: {', '.join(missing_completion)}"],
        })
    elif any(completion_checks.get(item) != "pass" for item in REQUIRED_D_CHECKS):
        checks.append({
            "id": "phase-d-completion-record",
            "status": "fail",
            "details": ["completion record contains non-pass D checks"],
        })
    else:
        checks.append({"id": "phase-d-completion-record", "status": "pass", "details": []})

    blocking = [
        f"{item['id']}: {', '.join(item['details'])}"
        for item in checks
        if item["status"] == "fail"
    ]
    return {"checks": checks, "blocking_items": blocking, "status": "complete" if not blocking else "blocked"}


def evaluate_phase_d(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    plan = load_yaml(project / "production" / "production-plan.yaml")
    readiness = load_yaml(project / "production" / "production-readiness.yaml")
    execution = load_yaml(project / "production" / "production-execution.yaml")
    cross_domain = load_yaml(project / "qa" / "cross-domain.yaml")
    production_qa = load_yaml(project / "qa" / "production-qa.yaml")
    completion = load_yaml(project / "production" / "phase-d-completion.yaml")

    for contract, document in (
        ("production-plan", plan),
        ("production-readiness", readiness),
        ("production-execution", execution),
        ("cross-domain-qa", cross_domain),
        ("production-qa", production_qa),
        ("phase-d-completion", completion),
    ):
        errors = validate_document(document, contract)
        if errors:
            raise PhaseDCompletionError(f"Invalid {contract}: " + "; ".join(errors))

    compiled, *_ = build_production_plan(client_id, root)
    if compiled != plan:
        raise PhaseDCompletionError("Committed production plan has drifted from the approved scope compiler")

    evaluated_readiness = evaluate_readiness(client_id, root)
    if evaluated_readiness != readiness:
        raise PhaseDCompletionError("Committed production readiness has drifted from the readiness gate")

    result = evaluate_documents(plan, readiness, execution, cross_domain, production_qa, completion)
    if completion.get("status") != result["status"]:
        result["blocking_items"].append("phase-d-completion.yaml status disagrees with evaluated result")
        result["status"] = "blocked"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate complete Phase D productionization")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = evaluate_phase_d(args.client, args.root)
        print(yaml.safe_dump(result, sort_keys=False))
        return 0 if result["status"] == "complete" else 2
    except PhaseDCompletionError as exc:
        print(f"phase-d-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
