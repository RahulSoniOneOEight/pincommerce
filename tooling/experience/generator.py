from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]


class ExperienceError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ExperienceError(f"Missing experience input: {path}")
    with path.open("r", encoding="utf-8") as fh:
        value = yaml.safe_load(fh)
    if not isinstance(value, dict):
        raise ExperienceError(f"Expected mapping in {path}")
    return value


def dump_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(value, fh, sort_keys=False)


def runtime_for_surface(surface: str) -> str:
    if surface in {"customer-app"}:
        return "flutter"
    if surface in {"web-store", "seller-portal", "commerce-admin", "ops-console", "analytics"}:
        return "web"
    if surface in {"erp", "warehouse", "customer-support"}:
        return "external"
    return "web"


def entry_for_surface(surface: str) -> str:
    mapping = {
        "customer-app": "apps/prototype_app",
        "web-store": "apps/storefront",
        "seller-portal": "apps/seller_portal",
        "commerce-admin": "apps/commerce_admin",
        "ops-console": "apps/ops_console",
        "analytics": "apps/analytics",
    }
    return mapping.get(surface, f"external/{surface}")


DIRECTIONS = [
    {
        "suffix": "A",
        "strategy": "discovery-first",
        "design_intent": {
            "density": "medium",
            "navigation": "category-led",
            "discovery": "editorial",
            "interaction": "guided",
        },
        "differentiators": [
            "strong merchandising and discovery",
            "category-led navigation",
            "guided conversion path",
        ],
    },
    {
        "suffix": "B",
        "strategy": "search-first",
        "design_intent": {
            "density": "compact",
            "navigation": "search-led",
            "discovery": "intent-driven",
            "interaction": "fast",
        },
        "differentiators": [
            "search and intent dominate entry",
            "faster route to product/action",
            "compact information density",
        ],
    },
    {
        "suffix": "C",
        "strategy": "task-first",
        "design_intent": {
            "density": "efficient",
            "navigation": "task-led",
            "discovery": "contextual",
            "interaction": "operational",
        },
        "differentiators": [
            "high-frequency tasks prioritized",
            "contextual discovery",
            "business/operational efficiency emphasis",
        ],
    },
]


def build_experience(client_id: str, root: Path = ROOT) -> dict[str, dict[str, Any]]:
    try:
        validate_identifier(client_id, kind="client_id")
    except IdentifierError as exc:
        raise ExperienceError(str(exc)) from exc

    project = root / "client-projects" / client_id
    surfaces = load_yaml(project / "derived" / "surface-map.yaml")
    journeys = load_yaml(project / "derived" / "journey-map.yaml")

    required_surfaces = list(surfaces.get("required", []))
    journey_ids = [
        item["id"] if isinstance(item, dict) else item
        for item in journeys.get("journeys", [])
    ]

    if not required_surfaces:
        raise ExperienceError("At least one required surface is needed")

    from tooling.experience.design_intelligence import build_design_intelligence

    files: dict[str, dict[str, Any]] = {}
    design_enabled = (project / "input" / "client-input.yaml").exists()
    if design_enabled:
        files.update(build_design_intelligence(client_id, root))
        base_visual_preset = files["experience/design/selection.yaml"]["preset"]
    else:
        # Lightweight generator/unit-test fixtures may omit onboarding input.
        # Real client projects include input/client-input.yaml and therefore
        # always receive governed Design Intelligence artifacts.
        base_visual_preset = "compact-commerce"
    fixture_set_id = "commerce-baseline"
    files["experience/fixtures/commerce-baseline.yaml"] = {
        "fixture_set_id": fixture_set_id,
        "client_id": client_id,
        "states": [
            {"id": "default", "purpose": "primary happy path", "data": {}},
            {"id": "loading", "purpose": "loading behavior", "data": {}},
            {"id": "empty", "purpose": "empty-state behavior", "data": {}},
            {"id": "failure", "purpose": "recoverable failure behavior", "data": {}},
            {"id": "approval-pending", "purpose": "business approval waiting state", "data": {}},
            {"id": "payment-failed", "purpose": "payment recovery state", "data": {}},
        ],
    }

    for definition in DIRECTIONS:
        direction_id = f"DIR-{client_id.upper().replace('_','-')}-{definition['suffix']}"
        direction = {
            "direction_id": direction_id,
            "client_id": client_id,
            "strategy": definition["strategy"],
            "surfaces": required_surfaces,
            "journey_emphasis": journey_ids,
            "design_intent": definition["design_intent"],
            "differentiators": definition["differentiators"],
            "fixture_set": fixture_set_id,
            **({
                "visual_preset": (
                    "premium-modern"
                    if definition["suffix"] == "A"
                    else "compact-commerce"
                    if definition["suffix"] == "B"
                    else base_visual_preset
                ),
                "design_selection_ref": "experience/design/selection.yaml",
                "theme_resolution_ref": "experience/design/theme-resolution.yaml",
                "asset_plan_ref": "experience/design/asset-plan.yaml",
                "motion_policy_ref": "design-intelligence/motion-policy.yaml",
            } if design_enabled else {}),
            "status": "draft",
        }
        suffix = definition["suffix"].lower()
        manifest = {
            "client_id": client_id,
            "direction_id": direction_id,
            "build_identity": "unbuilt",
            "requirements_source": "input/client-input.yaml#experience_requirements",
            "coverage_ref": f"experience/prototypes/{suffix}-coverage.yaml",
            "surfaces": [
                {
                    "id": surface,
                    "runtime": runtime_for_surface(surface),
                    "entry": entry_for_surface(surface),
                }
                for surface in required_surfaces
            ],
            "fixtures": [fixture_set_id],
            **({
                "design_selection_ref": "experience/design/selection.yaml",
                "theme_resolution_ref": "experience/design/theme-resolution.yaml",
                "asset_plan_ref": "experience/design/asset-plan.yaml",
            } if design_enabled else {}),
            "status": "draft",
        }
        files[f"experience/directions/{suffix}.yaml"] = direction
        files[f"experience/prototypes/{suffix}-manifest.yaml"] = manifest

    return files


def write_experience(client_id: str, root: Path = ROOT, overwrite: bool = False) -> list[Path]:
    project = root / "client-projects" / client_id
    files = build_experience(client_id, root)
    written: list[Path] = []
    for relative, value in files.items():
        path = project / relative
        if path.exists() and not overwrite:
            raise ExperienceError(f"Refusing to overwrite: {path}")
        dump_yaml(path, value)
        written.append(path)

    from tooling.experience.coverage import write_coverage
    for direction_file in ("a.yaml", "b.yaml", "c.yaml"):
        coverage_path = write_coverage(client_id, direction_file, root)
        written.append(coverage_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate experience directions and prototype manifests")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()

    try:
        files = build_experience(args.client, args.root)
        if args.print_only:
            print(yaml.safe_dump({"files": files}, sort_keys=False))
            return 0
        written = write_experience(args.client, args.root, args.overwrite)
        print(f"Generated {len(written)} experience artifacts for {args.client}.")
        return 0
    except ExperienceError as exc:
        print(f"experience-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
