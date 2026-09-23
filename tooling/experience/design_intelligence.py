from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]


class DesignIntelligenceError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DesignIntelligenceError(f"Missing design-intelligence input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DesignIntelligenceError(f"Expected mapping in {path}")
    return value


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def _platforms(surfaces: list[str]) -> list[str]:
    result = []
    if "customer-app" in surfaces:
        result.append("flutter")
    if any(s in surfaces for s in ("web-store", "seller-portal", "commerce-admin", "ops-console", "analytics")):
        result.append("web")
    return result or ["web"]


def _experience_types(client_input: dict[str, Any], surfaces: list[str]) -> list[str]:
    models = list(client_input.get("business_models", []))
    types = []
    for model in models:
        if model in {"d2c", "b2c"}:
            types.append("d2c-customer")
        elif model == "b2b":
            types.append("b2b-ordering")
        elif model in {"marketplace", "b2b-marketplace", "multi-vendor"}:
            types.append("marketplace")
    if "seller-portal" in surfaces:
        types.append("seller-operations")
    if any(s in surfaces for s in ("commerce-admin", "ops-console", "analytics")):
        types.append("admin-operations")
    return _unique(types)


def _default_preset(experience_types: list[str]) -> str:
    if any(x in experience_types for x in ("b2b-ordering", "seller-operations", "admin-operations")):
        return "compact-commerce"
    if "marketplace" in experience_types:
        return "editorial-commerce"
    return "premium-modern"


def _pattern_ids(client_input: dict[str, Any], capabilities: list[str]) -> list[str]:
    requested_components: list[str] = []
    for req in client_input.get("experience_requirements", []):
        if isinstance(req, dict):
            requested_components.extend(req.get("requested_components", []))

    patterns = []
    component_set = set(requested_components)
    if "catalogue" in capabilities or "product-card" in component_set:
        patterns.extend(["product-card", "category-rail"])
    if "checkout" in capabilities:
        patterns.append("checkout-section")
    if "quote-rfq" in capabilities or "reorder" in capabilities or "data-table" in component_set:
        patterns.append("b2b-quick-order")
    if "metric-card" in component_set or "analytics" in capabilities:
        patterns.append("dashboard-kpi")
    if "exception-table" in component_set or "ops-exceptions" in capabilities:
        patterns.append("exception-table")
    if any(x in capabilities for x in ("seller-settlements", "settlements", "payout-reconciliation")):
        patterns.append("seller-settlement")
    return _unique(patterns)


def build_design_intelligence(client_id: str, root: Path = ROOT) -> dict[str, dict[str, Any]]:
    try:
        validate_identifier(client_id, kind="client_id")
    except IdentifierError as exc:
        raise DesignIntelligenceError(str(exc)) from exc

    project = root / "client-projects" / client_id
    client_input = load_yaml(project / "input" / "client-input.yaml")
    surface_map = load_yaml(project / "derived" / "surface-map.yaml")
    capability_map = load_yaml(project / "derived" / "capability-map.yaml")
    def platform_yaml(relative: str) -> dict[str, Any]:
        candidate = root / relative
        return load_yaml(candidate if candidate.exists() else ROOT / relative)

    registry = platform_yaml("design-intelligence/component-registry.yaml")
    presets = platform_yaml("design-intelligence/visual-presets.yaml")
    asset_sources = platform_yaml("design-intelligence/asset-sources.yaml")
    default_theme = platform_yaml("design-contract/themes/default.yaml")

    surfaces = list(surface_map.get("required", []))
    capabilities = _unique(
        list(capability_map.get("mandatory", []))
        + list(capability_map.get("core", []))
        + list(capability_map.get("recommended", []))
        + list(capability_map.get("requested_additional", []))
    )
    platforms = _platforms(surfaces)
    experience_types = _experience_types(client_input, surfaces)
    preset = _default_preset(experience_types)

    explicit_sources = list(client_input.get("design_sources", []))
    sources = []
    for source in explicit_sources:
        sources.append({
            "id": source["id"],
            "type": source["type"],
            "ref": source["ref"],
            "authority": source.get("authority", "advisory"),
            "notes": source.get("notes", ""),
        })
    for index, ref in enumerate(client_input.get("source_refs", []), start=1):
        if not any(item["ref"] == ref for item in sources):
            sources.append({
                "id": f"source-ref-{index}",
                "type": "other",
                "ref": ref,
                "authority": "client-authoritative",
                "notes": "existing onboarding source reference",
            })

    inventory = {
        "inventory_id": f"DSI-{client_id}",
        "client_id": client_id,
        "sources": sources,
        "status": "evaluated",
    }

    platform_decisions: dict[str, Any] = {}
    for platform in platforms:
        pool = registry["platforms"][platform]
        platform_decisions[platform] = {
            "core": [item["id"] for item in pool["core"] if item.get("default")],
            "icons": [item["id"] for item in pool["icons"] if item.get("default")],
            "motion": [item["id"] for item in pool["motion"] if item.get("default")],
            "candidate_pool": {
                "core": [item["id"] for item in pool["core"]],
                "specialists": [item["id"] for item in pool.get("specialists", [])],
                "icons": [item["id"] for item in pool["icons"]],
                "motion": [item["id"] for item in pool["motion"]],
            },
        }

    patterns = []
    for pattern_id in _pattern_ids(client_input, capabilities):
        pattern = registry["patterns"][pattern_id]
        selected: dict[str, list[str]] = {}
        candidates: list[str] = []
        for platform in platforms:
            preferred = list(pattern.get("prefers", {}).get(platform, []))
            if preferred:
                selected[platform] = preferred
                candidates.extend(preferred)
        patterns.append({
            "pattern": pattern_id,
            "surface_role": pattern["role"],
            "selected": selected,
            "candidates": _unique(candidates),
            "reason": [
                "selected from approved registry by functional role",
                "wrapped behind PinCommerce shared design primitives",
                "semantic-token compatibility required",
                "production adoption remains subject to license/maintenance review",
            ],
        })

    selection = {
        "selection_id": f"DSEL-{client_id}",
        "client_id": client_id,
        "experience_type": experience_types,
        "preset": preset,
        "platforms": platform_decisions,
        "patterns": patterns,
        "quality_policy": {
            "minimum_score": registry["minimum_quality_score"],
            "weights": registry["quality_weights"],
            "rule": "deterministic checks plus rendered visual review; AI self-score alone is insufficient",
        },
        "status": "evaluated",
    }

    brand = client_input.get("brand", {}) or {}
    semantic = dict(default_theme.get("semantic_roles", {}))
    for role, value in (brand.get("semantic_overrides", {}) or {}).items():
        if role in semantic:
            semantic[role] = value

    theme = {
        "theme_id": f"THEME-{client_id}",
        "client_id": client_id,
        "preset": preset,
        "semantic_roles": semantic,
        "overrides": {
            "brand_raw_colors": brand.get("raw_colors", {}),
            "fonts": brand.get("fonts", []),
            "tone": brand.get("tone", []),
            "image_direction": brand.get("image_direction", []),
            "motion_preference": brand.get("motion_preference", "balanced"),
            "direction_overrides": {
                "A": {"preset": "premium-modern"},
                "B": {"preset": "compact-commerce"},
                "C": {"preset": preset},
            },
        },
        "status": "resolved",
    }

    has_client_media = any(item["type"] == "client-media" for item in sources)
    requests = []
    if any(x in capabilities for x in ("catalogue", "promotions")):
        base_query = " ".join(
            [str(client_input.get("industry", "commerce"))]
            + list(brand.get("image_direction", []))
            + list(brand.get("tone", []))
        ).strip()
        requests.extend([
            {
                "id": "homepage-hero",
                "purpose": "homepage-hero",
                "provider_policy": "client-assets-first; pexels-if-missing",
                "query": {
                    "text": base_query or "premium retail lifestyle",
                    "orientation": "landscape",
                    "candidate_count": 8,
                },
                "selected_asset": None,
                "status": "planned",
            },
            {
                "id": "category-editorial",
                "purpose": "category-editorial",
                "provider_policy": "client-assets-first; pexels-if-missing",
                "query": {
                    "text": base_query or "retail product lifestyle",
                    "orientation": "landscape",
                    "candidate_count": 8,
                },
                "selected_asset": None,
                "status": "planned",
            },
        ])

    assets = {
        "asset_plan_id": f"ASSET-{client_id}",
        "client_id": client_id,
        "source_order": asset_sources["selection_order"],
        "requests": requests,
        "client_media_present": has_client_media,
        "pexels": {
            "enabled": True,
            "api_key_ref": asset_sources["providers"]["pexels"]["api_key_ref"],
            "use_only_after": ["client-supplied", "existing-project-assets", "pincommerce-approved-fixtures"],
        },
        "status": "ready",
    }

    outputs = {
        "experience/design/source-inventory.yaml": inventory,
        "experience/design/selection.yaml": selection,
        "experience/design/theme-resolution.yaml": theme,
        "experience/design/asset-plan.yaml": assets,
    }
    contract_by_path = {
        "experience/design/source-inventory.yaml": "design-source-inventory",
        "experience/design/selection.yaml": "design-selection",
        "experience/design/theme-resolution.yaml": "theme-resolution",
        "experience/design/asset-plan.yaml": "asset-selection",
    }
    for path, document in outputs.items():
        errors = validate_document(document, contract_by_path[path])
        if errors:
            raise DesignIntelligenceError(f"Generated {path} invalid: " + "; ".join(errors))
    return outputs


def write_design_intelligence(client_id: str, root: Path = ROOT, overwrite: bool = False) -> list[Path]:
    project = root / "client-projects" / client_id
    outputs = build_design_intelligence(client_id, root)
    written = []
    for relative, value in outputs.items():
        path = project / relative
        if path.exists() and not overwrite:
            raise DesignIntelligenceError(f"Refusing to overwrite: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate UI/UX sources, components, themes and assets")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()
    try:
        outputs = build_design_intelligence(args.client, args.root)
        if args.print_only:
            print(yaml.safe_dump({"files": outputs}, sort_keys=False))
            return 0
        for path in write_design_intelligence(args.client, args.root, args.overwrite):
            print(path.relative_to(args.root))
        return 0
    except DesignIntelligenceError as exc:
        print(f"design-intelligence-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
