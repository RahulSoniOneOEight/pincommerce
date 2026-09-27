from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import hashlib
import yaml

from tooling.experience.penpot_bridge import verify_manifest
from tooling.review.visual_qa import REQUIRED_CHECKS

ROOT = Path(__file__).resolve().parents[2]


class ExperienceIntegrityError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ExperienceIntegrityError(f"Missing experience-integrity artifact: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExperienceIntegrityError(f"Expected mapping: {path}")
    return value


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _journey_index(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(j.get("id")): j for j in doc.get("journeys", []) if j.get("id")}


def _node_index(journey: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(n.get("id")): n for n in journey.get("nodes", []) if n.get("id")}


def _visual_qa(project: Path, required_surfaces: set[str]) -> tuple[list[str], dict[str, Any]]:
    qa_dir = project / "experience" / "visual-qa"
    records: dict[str, dict[str, Any]] = {}
    if qa_dir.exists():
        for path in sorted(qa_dir.glob("VQA-*.yaml")):
            record = _load(path)
            surface = str(record.get("surface") or "")
            if surface:
                records[surface] = record

    blockers: list[str] = []
    required_checks = set(REQUIRED_CHECKS)
    for surface in sorted(required_surfaces):
        record = records.get(surface)
        if not record:
            blockers.append(f"visual-qa missing for required surface {surface}")
            continue
        checks = {str(c.get("id")): str(c.get("status")) for c in record.get("checks", [])}
        missing = required_checks - set(checks)
        if missing:
            blockers.append(f"visual-qa {surface} missing checks: {', '.join(sorted(missing))}")
        incomplete = sorted(check for check in required_checks if checks.get(check) != "pass")
        if incomplete:
            blockers.append(f"visual-qa {surface} not passed: {', '.join(incomplete)}")
        if record.get("status") != "passed":
            blockers.append(f"visual-qa {surface} aggregate status is not passed")

    return blockers, {
        "required_surfaces": len(required_surfaces),
        "records_present": len(required_surfaces.intersection(records)),
        "all_required_checks": len(REQUIRED_CHECKS),
    }


def evaluate(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    graph = _load(project / "derived" / "journey-graph.yaml")
    surface_map = _load(project / "derived" / "surface-map.yaml")
    design_ir = _load(project / "experience" / "design" / "design-ir.yaml")
    components = _load(project / "experience" / "design" / "component-contract-registry.yaml")
    theme = _load(project / "experience" / "design" / "theme-resolution.yaml")
    manifest = _load(project / "experience" / "design" / "penpot-manifest.yaml")
    observed = _load(project / "experience" / "design" / "penpot-observed.yaml")

    blockers: list[str] = []

    required_surfaces = {str(x) for x in surface_map.get("required", [])}
    design_surfaces = {str(x) for x in design_ir.get("surfaces", [])}
    graph_surfaces = {
        str(node.get("surface"))
        for journey in graph.get("journeys", [])
        for node in journey.get("nodes", [])
        if node.get("surface")
    }
    manifest_surfaces = {str(x) for x in manifest.get("required_surfaces", [])}

    if design_surfaces != required_surfaces:
        blockers.append(
            "Design IR surfaces differ from required surface map: "
            f"required={sorted(required_surfaces)} design={sorted(design_surfaces)}"
        )
    if not graph_surfaces.issubset(required_surfaces):
        blockers.append(
            "Journey graph uses surfaces outside required surface map: "
            + ", ".join(sorted(graph_surfaces - required_surfaces))
        )
    if manifest_surfaces != required_surfaces:
        blockers.append(
            "Penpot manifest surfaces differ from required surface map: "
            f"required={sorted(required_surfaces)} manifest={sorted(manifest_surfaces)}"
        )

    graph_journeys = _journey_index(graph)
    design_journeys = _journey_index(design_ir)
    if set(graph_journeys) != set(design_journeys):
        blockers.append(
            "Design IR journey set differs from journey graph: "
            f"graph={sorted(graph_journeys)} design={sorted(design_journeys)}"
        )

    required_nodes = 0
    mapped_nodes = 0
    for journey_id, graph_journey in graph_journeys.items():
        graph_nodes = _node_index(graph_journey)
        required_nodes += len(graph_nodes)
        design_journey = design_journeys.get(journey_id)
        if not design_journey:
            continue
        design_nodes = _node_index(design_journey)
        mapped_nodes += len(set(graph_nodes).intersection(design_nodes))
        if set(graph_nodes) != set(design_nodes):
            blockers.append(
                f"{journey_id}: Design IR nodes differ from journey graph "
                f"(required={len(graph_nodes)} design={len(design_nodes)})"
            )
        for node_id, graph_node in graph_nodes.items():
            design_node = design_nodes.get(node_id)
            if not design_node:
                continue
            if graph_node.get("surface") != design_node.get("surface"):
                blockers.append(
                    f"{node_id}: surface mismatch graph={graph_node.get('surface')} "
                    f"design={design_node.get('surface')}"
                )
            if not design_node.get("component_refs"):
                blockers.append(f"{node_id}: no Design IR components mapped")
            if not design_node.get("state_refs"):
                blockers.append(f"{node_id}: no Design IR states mapped")

    manifest_journeys = {str(x) for x in manifest.get("required_journeys", [])}
    if manifest_journeys != set(graph_journeys):
        blockers.append(
            "Penpot manifest journeys differ from journey graph: "
            f"graph={sorted(graph_journeys)} manifest={sorted(manifest_journeys)}"
        )

    expected_hashes = {
        "design_ir": _hash(design_ir),
        "components": _hash(components),
        "theme": _hash(theme),
        "journeys": _hash(graph),
    }
    manifest_hashes = manifest.get("input_hashes", {})
    stale = sorted(key for key, value in expected_hashes.items() if manifest_hashes.get(key) != value)
    if stale:
        blockers.append("Penpot manifest is stale for inputs: " + ", ".join(stale))

    penpot_errors = verify_manifest(manifest, observed)
    blockers.extend(f"Penpot: {error}" for error in penpot_errors)

    qa_blockers, qa_summary = _visual_qa(project, required_surfaces)
    blockers.extend(qa_blockers)

    checks = {
        "surfaces": not any("surface" in x.lower() for x in blockers),
        "journeys": not any("journey" in x.lower() or "nodes differ" in x.lower() for x in blockers),
        "design_ir": mapped_nodes == required_nodes and required_nodes > 0 and not any("Design IR" in x for x in blockers),
        "penpot": not any(x.startswith("Penpot") for x in blockers),
        "visual_qa": not qa_blockers,
    }

    return {
        "client_id": client_id,
        "status": "passed" if not blockers else "blocked",
        "checks": checks,
        "coverage": {
            "required_surfaces": len(required_surfaces),
            "design_surfaces": len(design_surfaces),
            "journeys": len(graph_journeys),
            "required_nodes": required_nodes,
            "mapped_nodes": mapped_nodes,
            "visual_qa": qa_summary,
        },
        "blockers": blockers,
    }
