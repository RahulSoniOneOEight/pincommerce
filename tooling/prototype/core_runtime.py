from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]

BASELINES = {
    "medusa": "platform/prototype/baselines/medusa-standard-v1.yaml",
    "mercur": "platform/prototype/baselines/mercur-standard-v1.yaml",
    "tryton": "platform/prototype/baselines/tryton-standard-v1.yaml",
}

EXTERNAL_PROVIDER_BY_INTEGRATION = {
    "payment": "razorpay",
    "payments": "razorpay",
    "logistics": "shiprocket",
    "shipping": "shiprocket",
    "whatsapp": "meta-whatsapp-cloud",
    "messaging": "meta-whatsapp-cloud",
}


class CoreRuntimeError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CoreRuntimeError(f"Missing core runtime input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CoreRuntimeError(f"Expected mapping in {path}")
    return value


def _marketplace_required(client_input: dict[str, Any], solution: dict[str, Any]) -> bool:
    models = {str(item).lower() for item in client_input.get("business_models", [])}
    if models.intersection({"marketplace", "b2b-marketplace", "multi-vendor"}):
        return True
    return any(
        value.get("provider") == "mercur"
        for value in solution.get("providers", {}).values()
        if isinstance(value, dict)
    )


def _module_overrides(client_input: dict[str, Any], provider: str) -> list[dict[str, Any]]:
    result = []
    for index, item in enumerate(client_input.get("core_module_requirements", []), start=1):
        if not isinstance(item, dict) or item.get("module") != provider:
            continue
        result.append({
            "requirement_id": item.get("requirement_id", f"REQ-CORE-{index:03d}"),
            "target": item.get("target", "general"),
            "change": item["change"],
            "source_refs": list(item.get("source_refs", client_input.get("source_refs", []))),
        })
    return result


def build_core_runtime(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    client_input = load_yaml(project / "input" / "client-input.yaml")
    solution = load_yaml(project / "solution" / "solution-contract.yaml")

    solution_providers = {
        value.get("provider")
        for value in solution.get("providers", {}).values()
        if isinstance(value, dict)
    }

    requirements = {
        "medusa": "medusa" in solution_providers,
        "mercur": _marketplace_required(client_input, solution),
        "tryton": "tryton" in solution_providers,
    }

    modules = []
    for provider in ("medusa", "mercur", "tryton"):
        required = requirements[provider]
        modules.append({
            "provider": provider,
            "baseline_ref": BASELINES[provider],
            "required": required,
            "mode": "real-core" if required else "not-required",
            "overrides": _module_overrides(client_input, provider),
            "health": {
                "required": required,
                "evidence_ref": None,
            },
            "seed_evidence_ref": None,
            "status": "planned" if required else "not-required",
        })

    external = []
    seen = set()
    for raw in client_input.get("required_integrations", []):
        key = str(raw).lower()
        provider = EXTERNAL_PROVIDER_BY_INTEGRATION.get(key, key)
        if provider in seen:
            continue
        seen.add(provider)
        external.append({
            "provider": provider,
            "mode": "mock",
            "scenario_catalog_ref": "platform/prototype/mocks/provider-scenarios.yaml",
            "status": "ready",
        })

    value = {
        "runtime_id": f"PCR-{client_id}",
        "client_id": client_id,
        "modules": modules,
        "external_integrations": external,
        "demo_dataset_ref": f"experience/fixtures/{client_id}-demo-dataset.yaml",
        "status": "incomplete",
    }
    errors = validate_document(value, "prototype-core-runtime")
    if errors:
        raise CoreRuntimeError("Generated core runtime invalid: " + "; ".join(errors))
    return value


def evaluate_core_runtime(value: dict[str, Any]) -> dict[str, Any]:
    ready = True
    for module in value.get("modules", []):
        if not module.get("required"):
            continue
        if module.get("status") != "healthy":
            ready = False
        if not module.get("health", {}).get("evidence_ref"):
            ready = False
        if not module.get("seed_evidence_ref"):
            ready = False
    if not value.get("demo_dataset_ref"):
        ready = False
    value = dict(value)
    value["status"] = "prototype-ready" if ready else "incomplete"
    return value


def write_core_runtime(client_id: str, root: Path = ROOT, overwrite: bool = False) -> Path:
    project = root / "client-projects" / client_id
    path = project / "experience" / "prototype-core-runtime.yaml"
    if path.exists() and not overwrite:
        raise CoreRuntimeError(f"Refusing to overwrite: {path}")
    value = build_core_runtime(client_id, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def client_requires_core_runtime(client_id: str, root: Path = ROOT) -> bool:
    solution_path = root / "client-projects" / client_id / "solution" / "solution-contract.yaml"
    if not solution_path.exists():
        return False
    solution = load_yaml(solution_path)
    core = {"medusa", "mercur", "tryton"}
    return any(
        isinstance(value, dict) and value.get("provider") in core
        for value in solution.get("providers", {}).values()
    )


def assert_core_runtime_ready(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    path = root / "client-projects" / client_id / "experience" / "prototype-core-runtime.yaml"
    value = load_yaml(path)
    errors = validate_document(value, "prototype-core-runtime")
    if errors:
        raise CoreRuntimeError("Invalid core runtime: " + "; ".join(errors))
    evaluated = evaluate_core_runtime(value)
    dataset_ref = evaluated.get("demo_dataset_ref")
    if not dataset_ref:
        raise CoreRuntimeError("Core prototype runtime has no demo dataset reference")
    dataset_path = root / "client-projects" / client_id / dataset_ref
    dataset = load_yaml(dataset_path)
    dataset_errors = validate_document(dataset, "prototype-demo-dataset")
    if dataset_errors:
        raise CoreRuntimeError("Invalid prototype demo dataset: " + "; ".join(dataset_errors))
    if dataset.get("status") != "ready":
        raise CoreRuntimeError("Prototype demo dataset is not ready")

    mock_pending = [
        item.get("provider", "unknown")
        for item in evaluated.get("external_integrations", [])
        if item.get("status") != "ready"
    ]
    if mock_pending:
        raise CoreRuntimeError(
            "Prototype external integrations are not ready: " + ", ".join(mock_pending)
        )

    if evaluated["status"] != "prototype-ready":
        pending = [
            module["provider"]
            for module in evaluated["modules"]
            if module.get("required") and (
                module.get("status") != "healthy"
                or not module.get("health", {}).get("evidence_ref")
                or not module.get("seed_evidence_ref")
            )
        ]
        raise CoreRuntimeError(
            "Core prototype runtime is not ready; missing healthy runtime evidence for: "
            + ", ".join(pending)
        )
    return evaluated


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/evaluate core functional prototype runtime")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            assert_core_runtime_ready(args.client, args.root)
            print("Core prototype runtime is ready.")
            return 0
        path = write_core_runtime(args.client, args.root, args.overwrite)
        print(path.relative_to(args.root))
        return 0
    except CoreRuntimeError as exc:
        print(f"core-runtime-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
