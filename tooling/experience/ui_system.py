from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]

class UISystemError(RuntimeError): pass

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise UISystemError(f"Missing UI system input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise UISystemError(f"Expected mapping: {path}")
    return value

def _write(path: Path, value: dict[str, Any], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise UISystemError(f"Refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

def materialize(client_id: str, root: Path = ROOT, overwrite: bool = False) -> list[Path]:
    project = root / "client-projects" / client_id
    base = root / "platform" / "ui"

    master = deepcopy(_load(base / "master-design-system.yaml"))
    master["system_id"] = f"{client_id}-master-design-system"
    master["client_id"] = client_id

    theme_path = project / "experience" / "design" / "theme-resolution.yaml"
    if theme_path.exists():
        theme = _load(theme_path)
        master["resolved_theme_ref"] = "experience/design/theme-resolution.yaml"
        master["resolved_semantic_roles"] = theme.get("semantic_roles", {})

    registry = deepcopy(_load(base / "implementation-registry.yaml"))
    icons = deepcopy(_load(base / "icon-registry.yaml"))
    motion = deepcopy(_load(base / "motion-registry.yaml"))

    docs = [
        ("master-design-system", "experience/design/master-design-system.yaml", master),
        ("ui-implementation-registry", "experience/design/ui-implementation-registry.yaml", registry),
        ("icon-registry", "experience/design/icon-registry.yaml", icons),
        ("motion-registry", "experience/design/motion-registry.yaml", motion),
    ]
    written = []
    for kind, rel, doc in docs:
        errors = validate_document(doc, kind)
        if errors:
            raise UISystemError(f"Invalid {kind}: " + "; ".join(errors))
        path = project / rel
        _write(path, doc, overwrite)
        written.append(path)
    return written

def required_semantics(client_id: str, root: Path = ROOT) -> set[str]:
    p = root / "client-projects" / client_id
    design_ir = _load(p / "experience" / "design" / "design-ir.yaml")
    component_registry = _load(p / "experience" / "design" / "component-contract-registry.yaml")
    ids = set(design_ir.get("components", []))
    for item in component_registry.get("components", []):
        role = str(item.get("semantic_role") or "").strip().replace(" ", "-")
        if role:
            ids.add(role)
    return ids


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Materialize governed UI system contracts for a client")
    ap.add_argument("--client", required=True)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    try:
        for item in materialize(args.client, root=args.root, overwrite=args.overwrite):
            print(item.relative_to(args.root))
        return 0
    except UISystemError as exc:
        print(f"ui-system-error: {exc}")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
