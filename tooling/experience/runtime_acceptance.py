from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "design-intelligence" / "runtime-quality.yaml"


class RuntimeAcceptanceError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeAcceptanceError(f"Expected mapping in {path}")
    return value


def evaluate_runtime(root: Path = ROOT) -> dict[str, Any]:
    spec = _load(root / "design-intelligence" / "runtime-quality.yaml")
    flutter_path = root / spec["runtime"]["flutter"]
    web_path = root / spec["runtime"]["web"]
    widgetbook_path = root / spec["catalogs"]["flutter"]
    story_dir = root / spec["catalogs"]["web"]

    flutter = flutter_path.read_text(encoding="utf-8")
    web = web_path.read_text(encoding="utf-8")
    widgetbook = widgetbook_path.read_text(encoding="utf-8")
    stories = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(story_dir.glob("*.stories.tsx"))
    )
    css = (root / "packages/agency_web_ui/src/styles.css").read_text(encoding="utf-8")

    blockers: list[str] = []
    evidence: list[str] = []

    for pattern_id, pattern in spec.get("patterns", {}).items():
        flutter_symbol = str(pattern["flutter"])
        web_symbol = str(pattern["web"])
        if f"class {flutter_symbol}" not in flutter:
            blockers.append(f"{pattern_id}:flutter-symbol-missing")
        else:
            evidence.append(f"{pattern_id}:flutter")
        if f"function {web_symbol}" not in web:
            blockers.append(f"{pattern_id}:web-symbol-missing")
        else:
            evidence.append(f"{pattern_id}:web")
        if flutter_symbol not in widgetbook:
            blockers.append(f"{pattern_id}:widgetbook-missing")
        if web_symbol not in stories:
            blockers.append(f"{pattern_id}:storybook-missing")

    if "Semantics(" not in flutter:
        blockers.append("flutter:semantics-missing")
    else:
        evidence.append("flutter:semantics")
    if 'aria-label=' not in web and 'role="alert"' not in web:
        blockers.append("web:accessibility-semantics-missing")
    else:
        evidence.append("web:aria")
    if "prefers-reduced-motion" not in css:
        blockers.append("web:reduced-motion-missing")
    else:
        evidence.append("web:reduced-motion")

    viewports = spec.get("viewports", [])
    ids = {v.get("id") for v in viewports if isinstance(v, dict)}
    required_viewports = {"mobile-390", "tablet-768", "desktop-1440"}
    if not required_viewports.issubset(ids):
        blockers.append("capture-targets:incomplete")
    else:
        evidence.append("capture-targets:3")

    return {
        "status": "passed" if not blockers else "blocked",
        "patterns": len(spec.get("patterns", {})),
        "viewports": len(viewports),
        "evidence": evidence,
        "blocking_items": blockers,
    }


def main() -> int:
    result = evaluate_runtime()
    print(yaml.safe_dump(result, sort_keys=False))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
