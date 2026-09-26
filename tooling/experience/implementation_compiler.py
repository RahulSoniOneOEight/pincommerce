from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]

FLUTTER_PACKAGE_MAP = {
    "shadcn_flutter": "shadcn_flutter",
    "data_table_2": "data_table_2",
    "flutter_form_builder": "flutter_form_builder",
    "fl_chart": "fl_chart",
    "cached_network_image": "cached_network_image",
    "carousel_slider": "carousel_slider",
    "flutter_animate": "flutter_animate",
    "phosphor_flutter": "phosphor_flutter",
    "rive": "rive",
    "lottie": "lottie",
    "flutter_staggered_grid_view": "flutter_staggered_grid_view",
}
WEB_PACKAGE_MAP = {
    "base_ui": "@base-ui-components/react",
    "tanstack_table": "@tanstack/react-table",
    "tanstack_query": "@tanstack/react-query",
    "react_hook_form": "react-hook-form",
    "recharts": "recharts",
    "embla": "embla-carousel-react",
    "motion_react": "motion",
    "iconoir": "iconoir-react",
    "phosphor": "@phosphor-icons/react",
    "hugeicons": "@hugeicons/react",
    "sonner": "sonner",
    "rive": "@rive-app/react-canvas",
    "lottie": "lottie-react",
}


class DesignImplementationError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DesignImplementationError(f"Missing implementation input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DesignImplementationError(f"Expected mapping in {path}")
    return value


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def build_plan(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    selection = load_yaml(project / "experience" / "design" / "selection.yaml")
    if selection.get("client_id") != client_id:
        raise DesignImplementationError("selection client mismatch")

    platforms: dict[str, Any] = {}
    for platform, decision in selection.get("platforms", {}).items():
        chosen = list(decision.get("core", [])) + list(decision.get("icons", [])) + list(decision.get("motion", []))
        for pattern in selection.get("patterns", []):
            chosen.extend(pattern.get("selected", {}).get(platform, []))
        chosen = _unique(chosen)
        if platform == "flutter":
            packages = sorted({FLUTTER_PACKAGE_MAP[x] for x in chosen if x in FLUTTER_PACKAGE_MAP})
            platforms[platform] = {
                "shared_package": "packages/agency_flutter_ui",
                "dependency_candidates": packages,
                "wrapper_namespace": "PinCommerce",
                "catalog": "apps/widgetbook",
            }
        elif platform == "web":
            packages = sorted({WEB_PACKAGE_MAP[x] for x in chosen if x in WEB_PACKAGE_MAP})
            platforms[platform] = {
                "shared_package": "packages/agency_web_ui",
                "dependency_candidates": packages,
                "wrapper_namespace": "PinCommerce",
                "catalog": "apps/storybook",
            }

    patterns = []
    required_states = {
        "product-card": ["default","loading","error","out-of-stock","discounted"],
        "category-rail": ["default","loading","empty","error"],
        "b2b-quick-order": ["default","loading","empty","error","editing","validation-error"],
        "seller-settlement": ["default","loading","empty","error","pending","settled"],
        "dashboard-kpi": ["default","loading","empty","error"],
        "exception-table": ["default","loading","empty","error","open","resolved"],
        "checkout-section": ["default","loading","error","disabled","validation-error"],
    }
    for item in selection.get("patterns", []):
        pattern_id = item["pattern"]
        patterns.append({
            "id": pattern_id,
            "selected": item.get("selected", {}),
            "wrapper_name": "".join(part.title() for part in pattern_id.split("-")),
            "required_states": required_states.get(pattern_id, ["default","loading","empty","error"]),
            "requirements": [
                "semantic-token-only",
                "semantic-icons-only",
                "reduced-motion",
                "responsive",
                "accessibility",
                "catalog-story",
                "golden-or-screenshot",
                "quality-threshold",
            ],
        })

    plan = {
        "plan_id": f"DIMP-{client_id}",
        "client_id": client_id,
        "selection_ref": "experience/design/selection.yaml",
        "platforms": platforms,
        "patterns": patterns,
        "gates": [
            "dependency-health",
            "license-review",
            "state-completeness",
            "semantic-token-lint",
            "accessibility",
            "performance-budget",
            "visual-qa",
            "quality-threshold",
        ],
        "status": "ready" if platforms else "blocked",
    }
    errors = validate_document(plan, "design-implementation-plan")
    if errors:
        raise DesignImplementationError("Invalid design implementation plan: " + "; ".join(errors))
    return plan


def scaffold_manifest(plan: dict[str, Any]) -> dict[str, Any]:
    files = []
    for pattern in plan.get("patterns", []):
        wrapper = pattern["wrapper_name"]
        if "flutter" in plan.get("platforms", {}):
            files.append({
                "platform":"flutter",
                "pattern":pattern["id"],
                "target":f"packages/agency_flutter_ui/lib/src/patterns/{pattern['id'].replace('-', '_')}.dart",
                "wrapper":f"PinCommerce{wrapper}",
                "states":pattern["required_states"],
            })
        if "web" in plan.get("platforms", {}):
            files.append({
                "platform":"web",
                "pattern":pattern["id"],
                "target":f"packages/agency_web_ui/src/patterns/{pattern['id']}.tsx",
                "wrapper":f"PinCommerce{wrapper}",
                "states":pattern["required_states"],
            })
    return {
        "client_id":plan["client_id"],
        "implementation_plan_id":plan["plan_id"],
        "files":files,
        "rules":[
            "scaffold-does-not-bypass-human-reviewed-dependency-adoption",
            "wrappers-consume-semantic-tokens-and-semantic-icons",
            "catalog-and-test-evidence-required-before-approved",
        ],
    }


def write_plan(client_id: str, root: Path = ROOT, overwrite: bool = False) -> list[Path]:
    project = root / "client-projects" / client_id / "experience" / "design"
    plan = build_plan(client_id, root)
    outputs = {
        project / "implementation-plan.yaml": plan,
        project / "scaffold-manifest.yaml": scaffold_manifest(plan),
    }
    written = []
    for path, value in outputs.items():
        if path.exists() and not overwrite:
            raise DesignImplementationError(f"Refusing to overwrite: {path}")
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile selected Design Intelligence into implementation actions")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--print-only", action="store_true")
    args = parser.parse_args()
    try:
        plan = build_plan(args.client, args.root)
        if args.print_only:
            print(yaml.safe_dump({"plan":plan,"scaffold":scaffold_manifest(plan)}, sort_keys=False))
            return 0
        for path in write_plan(args.client, args.root, args.overwrite):
            print(path.relative_to(args.root))
        return 0
    except DesignImplementationError as exc:
        print(f"design-implementation-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
