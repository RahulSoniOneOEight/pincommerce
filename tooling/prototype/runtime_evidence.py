from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.prototype.core_runtime import CoreRuntimeError, evaluate_core_runtime

ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CoreRuntimeError(f"Expected mapping in {path}")
    return value


def record_runtime_evidence(
    client_id: str,
    provider: str,
    health_ref: str,
    seed_ref: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    path = root / "client-projects" / client_id / "experience" / "prototype-core-runtime.yaml"
    if not path.exists():
        raise CoreRuntimeError(f"Missing core runtime: {path}")
    value = load_yaml(path)
    matched = False
    for module in value.get("modules", []):
        if module.get("provider") != provider:
            continue
        if not module.get("required"):
            raise CoreRuntimeError(f"{provider} is not required for this client")
        module["health"]["evidence_ref"] = health_ref
        module["seed_evidence_ref"] = seed_ref
        module["status"] = "healthy"
        matched = True
        break
    if not matched:
        raise CoreRuntimeError(f"Unknown core provider: {provider}")

    value = evaluate_core_runtime(value)
    errors = validate_document(value, "prototype-core-runtime")
    if errors:
        raise CoreRuntimeError("Invalid core runtime after evidence update: " + "; ".join(errors))
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Record functional prototype core runtime evidence")
    parser.add_argument("--client", required=True)
    parser.add_argument("--provider", required=True, choices=["medusa", "mercur", "tryton"])
    parser.add_argument("--health-ref", required=True)
    parser.add_argument("--seed-ref", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        value = record_runtime_evidence(
            args.client, args.provider, args.health_ref, args.seed_ref, args.root
        )
        print(yaml.safe_dump({"status": value["status"]}, sort_keys=False))
        return 0
    except CoreRuntimeError as exc:
        print(f"runtime-evidence-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
