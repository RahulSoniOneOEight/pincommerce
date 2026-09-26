from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[2]

class SynthesisError(RuntimeError):
    pass

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SynthesisError(f"Missing synthesis input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SynthesisError(f"Expected mapping: {path}")
    return value

def synthesize(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    p = root / "client-projects" / client_id
    truth = _load(p / "derived" / "truth-register.yaml")
    graph = _load(p / "derived" / "journey-graph.yaml")
    refs = _load(p / "experience" / "references" / "adaptation.yaml")
    benchmark = _load(p / "derived" / "benchmark-report.yaml")
    unresolved = [
        f"{source.get('source_id')}:{pattern.get('id')}"
        for source in refs.get("sources", [])
        for pattern in source.get("patterns", [])
        if pattern.get("decision") not in {"REUSE","ADAPT","COMBINE","MODERNIZE","REJECT","BUILD_NEW"}
    ]
    if unresolved:
        raise SynthesisError("Reference decisions incomplete: " + ", ".join(unresolved))
    principles = [
        "client truth over reference imitation",
        "journey before screen",
        "reuse before custom build",
        "provider-neutral experience",
        "accessible responsive states",
    ]
    opportunities = []
    for source in refs.get("sources", []):
        for pattern in source.get("patterns", []):
            if pattern.get("decision") in {"REUSE","ADAPT","COMBINE","MODERNIZE"}:
                opportunities.append({
                    "source": source["source_id"],
                    "pattern": pattern["id"],
                    "decision": pattern["decision"],
                    "journeys": pattern.get("journeys", []),
                })
    directions = {
        "A": {"strategy": "conversion-first", "density": "balanced", "navigation": "guided", "reference_usage": "selective"},
        "B": {"strategy": "utility-first", "density": "compact", "navigation": "task-oriented", "reference_usage": "reuse-heavy"},
        "C": {"strategy": "brand-and-discovery-first", "density": "editorial", "navigation": "exploratory", "reference_usage": "adapt-and-combine"},
    }
    return {
        "client_id": client_id,
        "principles": principles,
        "truth_summary": {
            "facts": len(truth.get("facts", [])),
            "assumptions": len(truth.get("assumptions", [])),
            "unknowns": len(truth.get("unknowns", [])),
            "conflicts": len(truth.get("conflicts", [])),
        },
        "journey_priorities": [{"journey": x["id"], "surfaces": x.get("surfaces", []), "node_count": len(x.get("nodes", []))} for x in graph.get("journeys", [])],
        "reference_opportunities": opportunities,
        "benchmark_ref": "derived/benchmark-report.yaml",
        "directions": directions,
        "status": "review-ready",
    }
