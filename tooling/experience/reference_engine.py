from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from tooling.experience.reference_patterns import extract_patterns, DECISIONS

ROOT = Path(__file__).resolve().parents[2]

class ReferenceEngineError(RuntimeError):
    pass

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ReferenceEngineError(f"Missing reference input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReferenceEngineError(f"Expected mapping: {path}")
    return value

def analyze(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    inventory = _load(project / "experience" / "design" / "source-inventory.yaml")
    graph = _load(project / "derived" / "journey-graph.yaml")
    required_surfaces = list(_load(project / "derived" / "surface-map.yaml").get("required", []))
    source_dir = project / "experience" / "design" / "sources"
    journey_ids = [x["id"] for x in graph.get("journeys", [])]
    sources = []
    blockers = []
    for source in inventory.get("sources", []):
        source_id = str(source["id"])
        candidates = [source_dir / f"{source_id}.yaml", source_dir / f"{source_id}.yml"]
        source_path = next((x for x in candidates if x.exists()), None)
        if not source_path:
            blockers.append({"source_id": source_id, "reason": "normalized source evidence missing"})
            sources.append({"source_id": source_id, "ref": source.get("ref"), "patterns": [], "status": "blocked"})
            continue
        normalized = _load(source_path)
        patterns = extract_patterns(normalized)
        if not patterns:
            blockers.append({"source_id": source_id, "reason": "no evidenced patterns extracted"})
        sources.append({
            "source_id": source_id,
            "ref": source.get("ref"),
            "patterns": [
                {
                    **pattern,
                    "journeys": journey_ids,
                    "surfaces": required_surfaces,
                    "decision": None,
                    "reason": "Decision required after objective/journey fit review.",
                    "implementation_target": None,
                } for pattern in patterns
            ],
            "status": "analyzed" if patterns else "blocked",
        })
    return {"client_id": client_id, "sources": sources, "blockers": blockers, "status": "analyzed" if not blockers else "blocked"}

def apply_decisions(analysis: dict[str, Any], decisions: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    blockers = []
    sources = []
    for source in analysis.get("sources", []):
        source_decisions = decisions.get(source["source_id"], {})
        patterns = []
        for pattern in source.get("patterns", []):
            choice = source_decisions.get(pattern["id"], {})
            decision = choice.get("decision")
            if decision not in DECISIONS:
                blockers.append({"source_id": source["source_id"], "pattern_id": pattern["id"], "reason": "explicit decision required"})
            patterns.append({
                **pattern,
                "decision": decision,
                "reason": str(choice.get("reason") or pattern["reason"]),
                "implementation_target": choice.get("implementation_target"),
            })
        sources.append({"source_id": source["source_id"], "ref": source["ref"], "patterns": patterns})
    if analysis.get("blockers"):
        blockers.extend(analysis["blockers"])
    return {"client_id": analysis["client_id"], "sources": sources, "blockers": blockers, "status": "evaluated" if not blockers else "blocked"}
