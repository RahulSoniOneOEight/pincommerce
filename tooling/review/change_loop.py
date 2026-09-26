from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from tooling.review.impact import analyze_change

ROOT = Path(__file__).resolve().parents[2]

class ChangeLoopError(RuntimeError):
    pass

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ChangeLoopError(f"Missing change-loop input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ChangeLoopError(f"Expected mapping: {path}")
    return value

def plan(client_id: str, feedback_refs: list[str], root: Path = ROOT) -> dict[str, Any]:
    p = root / "client-projects" / client_id
    graph = _load(p / "derived" / "journey-graph.yaml")
    feedback = [_load(p / ref) for ref in feedback_refs]
    surfaces = sorted({x.get("surface") for x in feedback if x.get("surface")})
    journeys = sorted({x.get("journey") for x in feedback if x.get("journey")})
    screens = sorted({x.get("screen") for x in feedback if x.get("screen")})
    components = sorted({x.get("component") for x in feedback if x.get("component")})
    capabilities = set()
    affected_nodes = []
    for journey in graph.get("journeys", []):
        if journey["id"] not in journeys and journeys:
            continue
        for node in journey.get("nodes", []):
            if surfaces and node.get("surface") not in surfaces:
                continue
            if screens and node.get("screen") not in screens:
                continue
            capabilities.add(node.get("capability"))
            affected_nodes.append(node["id"])
    capabilities.discard(None)
    impact = analyze_change(client_id, sorted(capabilities), surfaces, root)
    qa = {"design": bool(components or screens or surfaces), "journey": bool(journeys or affected_nodes), "visual": True, "runtime": bool(impact["affected_integrations"] or impact["affected_entities"])}
    regenerate = []
    if qa["design"]: regenerate += ["experience/design/design-ir.yaml","experience/design/component-contract-registry.yaml"]
    if qa["journey"]: regenerate += ["derived/journey-graph.yaml"]
    if impact["affected_integrations"]: regenerate += ["derived/integration-map.yaml"]
    return {
        "client_id": client_id,
        "feedback_refs": feedback_refs,
        "affected_surfaces": surfaces,
        "affected_journeys": journeys,
        "affected_nodes": affected_nodes,
        "affected_components": components,
        "impact": impact,
        "regenerate": list(dict.fromkeys(regenerate)),
        "required_qa": [k for k,v in qa.items() if v],
        "approval_invalidated": True,
        "status": "planned",
    }
