from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]

CONTRACTS = {
    "client-input": ROOT / "contracts" / "schemas" / "client-input.schema.json",
    "truth-register": ROOT / "contracts" / "schemas" / "truth-register.schema.json",
    "integration-map": ROOT / "contracts" / "schemas" / "integration-map.schema.json",
    "architecture-decision": ROOT / "contracts" / "schemas" / "architecture-decision.schema.json",
    "scope-baseline": ROOT / "contracts" / "schemas" / "scope-baseline.schema.json",
    "current-scope": ROOT / "contracts" / "schemas" / "current-scope.schema.json",
    "production-plan": ROOT / "contracts" / "schemas" / "production-plan.schema.json",
    "production-readiness": ROOT / "contracts" / "schemas" / "production-readiness.schema.json",
    "production-migration-plan": ROOT / "contracts" / "schemas" / "production-migration-plan.schema.json",
    "production-provider-selections": ROOT / "contracts" / "schemas" / "production-provider-selections.schema.json",
    "production-execution": ROOT / "contracts" / "schemas" / "production-execution.schema.json",
    "cross-domain-qa": ROOT / "contracts" / "schemas" / "cross-domain-qa.schema.json",
    "phase-d-completion": ROOT / "contracts" / "schemas" / "phase-d-completion.schema.json",
    "production-qa": ROOT / "contracts" / "schemas" / "production-qa.schema.json",
    "solution": ROOT / "contracts" / "schemas" / "solution-contract.schema.json",
    "workflow-state": ROOT / "contracts" / "schemas" / "workflow-state.schema.json",
    "change": ROOT / "contracts" / "schemas" / "change-contract.schema.json",
    "review-artifact": ROOT / "contracts" / "schemas" / "review-artifact.schema.json",
    "ai-proposal": ROOT / "contracts" / "schemas" / "ai-proposal.schema.json",
    "experience-direction": ROOT / "contracts" / "schemas" / "experience-direction.schema.json",
    "prototype-manifest": ROOT / "contracts" / "schemas" / "prototype-manifest.schema.json",
    "prototype-coverage": ROOT / "contracts" / "schemas" / "prototype-coverage.schema.json",
    "prototype-implementation": ROOT / "contracts" / "schemas" / "prototype-implementation.schema.json",
    "prototype-core-runtime": ROOT / "contracts" / "schemas" / "prototype-core-runtime.schema.json",
    "prototype-demo-dataset": ROOT / "contracts" / "schemas" / "prototype-demo-dataset.schema.json",
    "fixture-set": ROOT / "contracts" / "schemas" / "fixture-set.schema.json",
    "visual-qa": ROOT / "contracts" / "schemas" / "visual-qa.schema.json",
    "build-identity": ROOT / "contracts" / "schemas" / "build-identity.schema.json",
    "review-session": ROOT / "contracts" / "schemas" / "review-session.schema.json",
    "prototype-revision": ROOT / "contracts" / "schemas" / "prototype-revision.schema.json",
    "review-feedback": ROOT / "contracts" / "schemas" / "review-feedback.schema.json",
    "review-round": ROOT / "contracts" / "schemas" / "review-round.schema.json",
    "live-review-session": ROOT / "contracts" / "schemas" / "live-review-session.schema.json",
    "bugdrop": ROOT / "contracts" / "schemas" / "bugdrop.schema.json",
    "capture-manifest": ROOT / "contracts" / "schemas" / "capture-manifest.schema.json",
    "domain-event": ROOT / "contracts" / "schemas" / "domain-event.schema.json",
    "domain-command": ROOT / "contracts" / "schemas" / "domain-command.schema.json",
    "reconciliation-record": ROOT / "contracts" / "schemas" / "reconciliation-record.schema.json",
    "provider-adapter": ROOT / "contracts" / "schemas" / "provider-adapter.schema.json",
    "dead-letter": ROOT / "contracts" / "schemas" / "dead-letter.schema.json",
    "health-record": ROOT / "contracts" / "schemas" / "health-record.schema.json",
    "release-candidate": ROOT / "contracts" / "schemas" / "release-candidate.schema.json",
    "hardening-evidence": ROOT / "contracts" / "schemas" / "hardening-evidence.schema.json",
    "uat-record": ROOT / "contracts" / "schemas" / "uat-record.schema.json",
    "production-authorization": ROOT / "contracts" / "schemas" / "production-authorization.schema.json",
    "release-record": ROOT / "contracts" / "schemas" / "release-record.schema.json",
    "recovery-record": ROOT / "contracts" / "schemas" / "recovery-record.schema.json",
    "observability-evidence": ROOT / "contracts" / "schemas" / "observability-evidence.schema.json",
    "staging-validation": ROOT / "contracts" / "schemas" / "staging-validation.schema.json",
    "staging-manifest": ROOT / "contracts" / "schemas" / "staging-manifest.schema.json",
    "provider-sandbox-evidence": ROOT / "contracts" / "schemas" / "provider-sandbox-evidence.schema.json",
    "staging-runtime-evidence": ROOT / "contracts" / "schemas" / "staging-runtime-evidence.schema.json",
    "staging-import-evidence": ROOT / "contracts" / "schemas" / "staging-import-evidence.schema.json",
    "staging-e2e-evidence": ROOT / "contracts" / "schemas" / "staging-e2e-evidence.schema.json",
    "data-contract": ROOT / "contracts" / "schemas" / "data-contract.schema.json",
    "business-contract": ROOT / "contracts" / "schemas" / "business-contract.schema.json",
    "ai-decision": ROOT / "contracts" / "schemas" / "ai-decision.schema.json",
    "design-source-inventory": ROOT / "contracts" / "schemas" / "design-source-inventory.schema.json",
    "design-selection": ROOT / "contracts" / "schemas" / "design-selection.schema.json",
    "theme-resolution": ROOT / "contracts" / "schemas" / "theme-resolution.schema.json",
    "asset-selection": ROOT / "contracts" / "schemas" / "asset-selection.schema.json",
    "design-quality-evaluation": ROOT / "contracts" / "schemas" / "design-quality-evaluation.schema.json",
    "design-implementation-plan": ROOT / "contracts" / "schemas" / "design-implementation-plan.schema.json",
    "component-benchmark": ROOT / "contracts" / "schemas" / "component-benchmark.schema.json",
    "design-health": ROOT / "contracts" / "schemas" / "design-health.schema.json",
    "design-outcome": ROOT / "contracts" / "schemas" / "design-outcome.schema.json",
    "design-contract": ROOT / "contracts" / "schemas" / "design-contract.schema.json",
    "integration-contract": ROOT / "contracts" / "schemas" / "integration-contract.schema.json",
    "component-selection-ledger": ROOT / "contracts" / "schemas" / "component-selection-ledger.schema.json",
}


class ContractValidationError(RuntimeError):
    pass


def load_document(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        if path.suffix == ".json":
            return json.load(fh)
        return yaml.safe_load(fh)


def validate_document(document: Any, contract_type: str) -> list[str]:
    if contract_type not in CONTRACTS:
        raise ContractValidationError(f"Unknown contract type: {contract_type}")
    schema = load_document(CONTRACTS[contract_type])
    validator = Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    ]


def validate(path: Path, contract_type: str) -> list[str]:
    return validate_document(load_document(path), contract_type)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Agency Platform V2 contracts")
    parser.add_argument("contract_type", choices=sorted(CONTRACTS))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    errors = validate(args.path, args.contract_type)
    if errors:
        print(f"{args.path}: invalid {args.contract_type} contract")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"{args.path}: valid {args.contract_type} contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
