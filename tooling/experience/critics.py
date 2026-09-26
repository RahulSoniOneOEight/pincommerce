from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[2]

class CriticError(RuntimeError):
    pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise CriticError(f"Missing critic input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise CriticError(f"Expected mapping: {path}")
    return value

def design_critic(client_id:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    ir=_load(p/"experience"/"design"/"design-ir.yaml")
    reg=_load(p/"experience"/"design"/"component-contract-registry.yaml")
    theme=_load(p/"experience"/"design"/"theme-resolution.yaml")
    known={x["id"]:x for x in reg.get("components",[])}
    findings=[]
    for journey in ir.get("journeys",[]):
        for node in journey.get("nodes",[]):
            if not node.get("component_refs"): findings.append({"severity":"blocker","node":node["id"],"issue":"no component mapped"})
            for ref in node.get("component_refs",[]):
                if ref not in known: findings.append({"severity":"blocker","node":node["id"],"issue":f"unknown component {ref}"})
            required={"default","loading","empty","failure"}
            missing=required-set(node.get("state_refs",[]))
            if missing: findings.append({"severity":"major","node":node["id"],"issue":"missing states: "+", ".join(sorted(missing))})
    if not theme.get("semantic_roles"): findings.append({"severity":"blocker","issue":"semantic color roles absent"})
    return {"client_id":client_id,"critic":"design","findings":findings,"status":"passed" if not any(x["severity"]=="blocker" for x in findings) else "blocked"}

def journey_critic(client_id:str,root:Path=ROOT)->dict[str,Any]:
    graph=_load(root/"client-projects"/client_id/"derived"/"journey-graph.yaml")
    findings=[]
    for journey in graph.get("journeys",[]):
        ids={x.get("id") for x in journey.get("nodes",[])}
        surfaces=set()
        for node in journey.get("nodes",[]):
            surfaces.add(node.get("surface"))
            for field in ("screen","backend_operation","success_state","error_state","branches","permission"):
                if not node.get(field): findings.append({"severity":"blocker","node":node.get("id"),"issue":f"missing {field}"})
            for target in node.get("next",[]):
                if target not in ids: findings.append({"severity":"blocker","node":node.get("id"),"issue":f"dead next target {target}"})
        declared=set(journey.get("surfaces",[]))
        if declared!=surfaces: findings.append({"severity":"major","journey":journey.get("id"),"issue":"declared surfaces do not match nodes"})
    return {"client_id":client_id,"critic":"journey","findings":findings,"status":"passed" if not any(x["severity"]=="blocker" for x in findings) else "blocked"}

def reference_critic(client_id:str,root:Path=ROOT)->dict[str,Any]:
    refs=_load(root/"client-projects"/client_id/"experience"/"references"/"adaptation.yaml")
    findings=[]
    for source in refs.get("sources",[]):
        if not source.get("patterns"): findings.append({"severity":"blocker","source":source.get("source_id"),"issue":"no extracted patterns"})
        for pattern in source.get("patterns",[]):
            if pattern.get("decision") not in {"REUSE","ADAPT","COMBINE","MODERNIZE","REJECT","BUILD_NEW"}:
                findings.append({"severity":"blocker","source":source.get("source_id"),"pattern":pattern.get("id"),"issue":"decision missing"})
            if not pattern.get("reason"): findings.append({"severity":"major","pattern":pattern.get("id"),"issue":"decision rationale missing"})
    return {"client_id":client_id,"critic":"reference","findings":findings,"status":"passed" if not any(x["severity"]=="blocker" for x in findings) else "blocked"}
