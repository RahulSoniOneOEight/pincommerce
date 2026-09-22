from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tooling.validation.identifiers import IdentifierError, validate_identifier
from tooling.onboarding.abc_completion import (
    architecture_decisions,
    build_integration_map,
    build_truth_register,
    classification_evidence,
    enrich_capability_gap,
)

ROOT = Path(__file__).resolve().parents[2]

BUSINESS_MODEL_TO_ARCHETYPE = {
    "d2c": "d2c-commerce",
    "b2c": "d2c-commerce",
    "b2b": "b2b-commerce",
    "marketplace": "marketplace",
}


class OnboardingError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise OnboardingError(f"Missing required input: {path}")
    with path.open("r", encoding="utf-8") as fh:
        value = yaml.safe_load(fh)
    if not isinstance(value, dict):
        raise OnboardingError(f"Expected mapping in {path}")
    return value


def dump_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(value, fh, sort_keys=False)


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def classify_archetypes(business_models: list[str]) -> list[str]:
    return unique(
        [BUSINESS_MODEL_TO_ARCHETYPE[m] for m in business_models if m in BUSINESS_MODEL_TO_ARCHETYPE]
    )


def load_industry_profile(root: Path, industry: str) -> dict[str, Any]:
    return load_yaml(root / "intelligence" / "industries" / industry / "profile.yaml")


def load_archetype(root: Path, archetype: str) -> dict[str, Any]:
    path = root / "intelligence" / "archetypes" / f"{archetype}.yaml"
    if not path.exists():
        return {
            "id": archetype,
            "expected_surfaces": [],
            "optional_surfaces": [],
            "journeys": [],
            "core_capabilities": [],
            "recommended_capabilities": [],
        }
    return load_yaml(path)


def resolve_benchmark(
    client_input: dict[str, Any],
    industry_profile: dict[str, Any],
    archetypes: list[dict[str, Any]],
) -> dict[str, Any]:
    industry_core = list(industry_profile.get("core_capabilities", []))
    industry_recommended = list(industry_profile.get("recommended_capabilities", []))
    archetype_core: list[str] = []
    archetype_recommended: list[str] = []
    journeys: list[str] = []
    surfaces: list[str] = []
    optional_surfaces: list[str] = []

    for archetype in archetypes:
        archetype_core.extend(archetype.get("core_capabilities", []))
        archetype_recommended.extend(archetype.get("recommended_capabilities", []))
        journeys.extend(archetype.get("journeys", []))
        surfaces.extend(archetype.get("expected_surfaces", []))
        optional_surfaces.extend(archetype.get("optional_surfaces", []))

    expected_surfaces = unique(surfaces)
    expected_optional = [
        s for s in unique(optional_surfaces) if s not in set(expected_surfaces)
    ]

    return {
        "client_id": client_input["client_id"],
        "industry": client_input["industry"],
        "archetypes": [a["id"] for a in archetypes],
        "expected": {
            "core_capabilities": unique(industry_core + archetype_core),
            "recommended_capabilities": unique(industry_recommended + archetype_recommended),
            "journeys": unique(journeys),
            "surfaces": expected_surfaces,
            "optional_surfaces": expected_optional,
            "controls": unique(list(industry_profile.get("controls", []))),
            "qa_emphasis": unique(list(industry_profile.get("qa_emphasis", []))),
        },
    }


def resolve_capability_gap(
    client_input: dict[str, Any],
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    requested = set(client_input.get("requested_capabilities", []))
    core = benchmark["expected"]["core_capabilities"]
    recommended = benchmark["expected"]["recommended_capabilities"]

    return {
        "client_id": client_input["client_id"],
        "requested": sorted(requested),
        "core_missing": [c for c in core if c not in requested],
        "recommended_missing": [c for c in recommended if c not in requested],
        "covered_by_request": [c for c in core + recommended if c in requested],
        "not_in_reference_baseline": [
            c for c in sorted(requested) if c not in set(core + recommended)
        ],
    }


def resolve_capability_map(
    client_input: dict[str, Any],
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    requested = set(client_input.get("requested_capabilities", []))
    core = benchmark["expected"]["core_capabilities"]
    recommended = benchmark["expected"]["recommended_capabilities"]

    return {
        "client_id": client_input["client_id"],
        "mandatory": ["authentication", "audit"],
        "core": unique(core),
        "recommended": unique(recommended),
        "requested_additional": [
            c for c in sorted(requested) if c not in set(core + recommended)
        ],
        "later": [],
        "not_applicable": [],
    }


def resolve_journey_map(
    client_input: dict[str, Any],
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    return {
        "client_id": client_input["client_id"],
        "journeys": [
            {"id": journey, "status": "required"}
            for journey in benchmark["expected"]["journeys"]
        ],
    }


def resolve_surface_map(
    client_input: dict[str, Any],
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    return {
        "client_id": client_input["client_id"],
        "required": benchmark["expected"]["surfaces"],
        "recommended": benchmark["expected"]["optional_surfaces"],
    }


def infer_entity_map(client_id: str, capabilities: list[str]) -> dict[str, Any]:
    entities: dict[str, dict[str, str]] = {}
    if any(c in capabilities for c in ("orders", "checkout", "return-refund")):
        entities["order"] = {"owner_capability": "commerce-order-management"}
    if any(c in capabilities for c in ("inventory-availability",)):
        entities["inventory"] = {"owner_capability": "erp-inventory"}
    if any(c in capabilities for c in ("checkout", "return-refund")):
        entities["payment"] = {"owner_capability": "payment-integration"}
    if any(c in capabilities for c in ("fulfilment",)):
        entities["shipment"] = {"owner_capability": "logistics-integration"}
    if any(c in capabilities for c in ("b2b-account", "credit-management")):
        entities["business-account"] = {"owner_capability": "commerce-account-management"}
    return {"client_id": client_id, "entities": entities}


def infer_dependency_map(
    client_id: str,
    capabilities: list[str],
) -> dict[str, Any]:
    flows: list[dict[str, Any]] = []
    if "checkout" in capabilities:
        flows.append(
            {
                "id": "checkout-to-accounting",
                "domains": ["experience", "commerce", "integration", "erp"],
            }
        )
    if "fulfilment" in capabilities:
        flows.append(
            {
                "id": "order-to-fulfilment",
                "domains": ["commerce", "integration", "erp"],
            }
        )
    if "return-refund" in capabilities:
        flows.append(
            {
                "id": "return-to-refund",
                "domains": ["experience", "commerce", "integration", "erp", "automation"],
            }
        )
    if "quote-rfq" in capabilities:
        flows.append(
            {
                "id": "quote-to-order",
                "domains": ["experience", "commerce", "automation", "erp"],
            }
        )
    return {"client_id": client_id, "critical_cross_domain_flows": flows}


def provider_rule_matches(
    rule: dict[str, Any],
    capabilities: set[str],
    surfaces: set[str],
) -> bool:
    if rule.get("always"):
        return True
    if "when_surface" in rule and rule["when_surface"] in surfaces:
        return True
    if "when_any_surface" in rule and any(s in surfaces for s in rule["when_any_surface"]):
        return True
    if "when_any_capability" in rule and any(
        c in capabilities for c in rule["when_any_capability"]
    ):
        return True
    return False


def resolve_solution_contract(
    client_id: str,
    capabilities: list[str],
    surfaces: list[str],
    root: Path,
) -> dict[str, Any]:
    rules = load_yaml(root / "platform" / "default-provider-rules.yaml")["rules"]
    providers: dict[str, dict[str, Any]] = {}
    capability_set, surface_set = set(capabilities), set(surfaces)

    for key, rule in rules.items():
        if provider_rule_matches(rule, capability_set, surface_set):
            provider = rule["provider"]
            providers[key] = {
                "type": provider["type"],
                "provider": provider["id"],
                "version": None,
                "extensions": [],
            }

    return {"version": 1, "client": client_id, "providers": providers}


def resolve_reuse_decisions(solution: dict[str, Any]) -> dict[str, Any]:
    return {
        "client_id": solution["client"],
        "decisions": {
            key: {
                "strategy": "reuse" if value["type"] != "experience" else "shared-platform",
                "provider": value["provider"],
            }
            for key, value in solution["providers"].items()
        },
    }


@dataclass
class GeneratedBlueprint:
    files: dict[str, dict[str, Any]]


def build_blueprint(client_id: str, root: Path = ROOT) -> GeneratedBlueprint:
    try:
        validate_identifier(client_id, kind="client_id")
    except IdentifierError as exc:
        raise OnboardingError(str(exc)) from exc

    project = root / "client-projects" / client_id
    client_input = load_yaml(project / "input" / "client-input.yaml")

    if client_input.get("client_id") != client_id:
        raise OnboardingError("client_id in input does not match project directory")

    industry = client_input["industry"]
    business_models = list(client_input.get("business_models", []))
    archetype_ids = classify_archetypes(business_models)

    industry_profile = load_industry_profile(root, industry)
    archetypes = [load_archetype(root, a) for a in archetype_ids]
    benchmark = resolve_benchmark(client_input, industry_profile, archetypes)
    capability_gap = resolve_capability_gap(client_input, benchmark)
    capability_gap_analysis = enrich_capability_gap(capability_gap)
    capability_map = resolve_capability_map(client_input, benchmark)
    journey_map = resolve_journey_map(client_input, benchmark)
    surface_map = resolve_surface_map(client_input, benchmark)

    active_capabilities = unique(
        capability_map["core"]
        + capability_map["recommended"]
        + capability_map["requested_additional"]
    )
    all_surfaces = unique(surface_map["required"] + surface_map["recommended"])
    entity_map = infer_entity_map(client_id, active_capabilities)
    dependency_map = infer_dependency_map(client_id, active_capabilities)
    integration_map = build_integration_map(client_input)
    solution = resolve_solution_contract(
        client_id, active_capabilities, all_surfaces, root
    )
    decisions = architecture_decisions(client_id, solution)
    reuse = resolve_reuse_decisions(solution)

    client_profile = {
        "client_id": client_id,
        "industry": industry,
        "business_models": business_models,
        "archetypes": archetype_ids,
        "geographies": client_input.get("geographies", []),
        "risk_profile": client_input.get("risk_profile", "standard"),
        "goals": client_input.get("goals", []),
        "existing_systems": client_input.get("existing_systems", []),
        "constraints": client_input.get("constraints", []),
        "required_integrations": client_input.get("required_integrations", []),
        "status": "normalized",
    }

    industry_profile_out = {
        "client_id": client_id,
        "industry": industry,
        "archetypes": archetype_ids,
        "business_models": business_models,
        "risk_profile": client_profile["risk_profile"],
        "benchmark_sources": [
            f"intelligence/industries/{industry}/profile.yaml",
            *[f"intelligence/archetypes/{a}.yaml" for a in archetype_ids],
        ],
    }

    truth_register = build_truth_register(client_input)

    files = {
        "derived/truth-register.yaml": truth_register,
        "derived/client-profile.yaml": client_profile,
        "derived/industry-profile.yaml": industry_profile_out,
        "derived/classification-evidence.yaml": {
            "client_id": client_id,
            **classification_evidence(business_models, archetype_ids),
        },
        "derived/benchmark-report.yaml": benchmark,
        "derived/capability-gap.yaml": capability_gap,
        "derived/capability-gap-analysis.yaml": capability_gap_analysis,
        "derived/reuse-decisions.yaml": reuse,
        "derived/capability-map.yaml": capability_map,
        "derived/journey-map.yaml": journey_map,
        "derived/entity-map.yaml": entity_map,
        "derived/surface-map.yaml": surface_map,
        "derived/dependency-map.yaml": dependency_map,
        "derived/integration-map.yaml": integration_map,
        "solution/solution-contract.yaml": solution,
        **{f"solution/decisions/{d['decision_id']}.yaml": d for d in decisions},
    }
    return GeneratedBlueprint(files=files)


def write_blueprint(
    client_id: str,
    root: Path = ROOT,
    overwrite: bool = False,
) -> list[Path]:
    blueprint = build_blueprint(client_id, root)
    project = root / "client-projects" / client_id
    written: list[Path] = []

    for relative, value in blueprint.files.items():
        path = project / relative
        if path.exists() and not overwrite:
            raise OnboardingError(
                f"Refusing to overwrite existing generated artifact: {path}. "
                "Use --overwrite for regeneration."
            )
        dump_yaml(path, value)
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a client delivery blueprint")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()

    try:
        blueprint = build_blueprint(args.client, args.root)
        if args.print_only:
            print(yaml.safe_dump({"files": blueprint.files}, sort_keys=False))
            return 0
        paths = write_blueprint(args.client, args.root, overwrite=args.overwrite)
        print(f"Generated {len(paths)} onboarding/solution artifacts for {args.client}.")
        for path in paths:
            print(path.relative_to(args.root))
        return 0
    except OnboardingError as exc:
        print(f"onboarding-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
