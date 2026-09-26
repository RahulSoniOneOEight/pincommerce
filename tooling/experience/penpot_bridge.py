from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[2]

class PenpotBridgeError(RuntimeError):
    pass

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PenpotBridgeError(f"Missing Penpot bridge input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PenpotBridgeError(f"Expected mapping: {path}")
    return value

def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def build_manifest(client_id: str, *, project_ref: str, revision_ref: str, root: Path = ROOT) -> dict[str, Any]:
    if not project_ref or not revision_ref:
        raise PenpotBridgeError("Real Penpot project_ref and revision_ref are required")
    p = root / "client-projects" / client_id
    design_ir = _load(p / "experience" / "design" / "design-ir.yaml")
    components = _load(p / "experience" / "design" / "component-contract-registry.yaml")
    theme = _load(p / "experience" / "design" / "theme-resolution.yaml")
    graph = _load(p / "derived" / "journey-graph.yaml")
    manifest = {
        "client_id": client_id,
        "project_ref": project_ref,
        "revision_ref": revision_ref,
        "input_hashes": {
            "design_ir": _hash(design_ir),
            "components": _hash(components),
            "theme": _hash(theme),
            "journeys": _hash(graph),
        },
        "required_surfaces": design_ir.get("surfaces", []),
        "required_journeys": [x["id"] for x in design_ir.get("journeys", [])],
        "required_components": design_ir.get("components", []),
        "requirements": {
            "components_editable": True,
            "responsive_variants": ["mobile", "tablet", "desktop"],
            "states": ["default", "loading", "empty", "error", "success", "disabled"],
            "interactive_journeys": True,
        },
        "status": "external-design-required",
    }
    return manifest

def verify_manifest(manifest: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    errors = []
    if observed.get("project_ref") != manifest.get("project_ref"):
        errors.append("Penpot project reference mismatch")
    if observed.get("revision_ref") != manifest.get("revision_ref"):
        errors.append("Penpot revision reference mismatch")
    observed_components = set(observed.get("components", []))
    missing = set(manifest.get("required_components", [])) - observed_components
    if missing:
        errors.append("Missing Penpot components: " + ", ".join(sorted(missing)))
    observed_journeys = set(observed.get("interactive_journeys", []))
    missing_journeys = set(manifest.get("required_journeys", [])) - observed_journeys
    if missing_journeys:
        errors.append("Missing interactive journeys: " + ", ".join(sorted(missing_journeys)))
    return errors
