from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[2]

class VisualCriticError(RuntimeError): pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise VisualCriticError(f"Missing critic input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise VisualCriticError(f"Expected mapping: {path}")
    return value

def evaluate(client_id:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    theme=_load(p/"experience"/"design"/"theme-resolution.yaml")
    assets=_load(p/"experience"/"design"/"asset-plan.yaml")
    ir=_load(p/"experience"/"design"/"design-ir.yaml")
    impl=_load(p/"experience"/"design"/"ui-implementation-registry.yaml")
    findings=[]
    roles=theme.get("semantic_roles",{})
    if len(roles)<5: findings.append({"severity":"blocker","issue":"semantic palette is too sparse","rule":"color-hierarchy"})
    unresolved=[x["id"] for x in assets.get("requests",[]) if x.get("status") in {"planned","blocked"}]
    if unresolved: findings.append({"severity":"major","issue":"unresolved imagery/assets: "+", ".join(unresolved),"rule":"imagery"})
    mapped={x["semantic_id"] for x in impl.get("components",[])}
    aliases={a for x in impl.get("components",[]) for a in x.get("aliases",[])}
    for j in ir.get("journeys",[]):
        for n in j.get("nodes",[]):
            if len(n.get("component_refs",[]))>8:
                findings.append({"severity":"major","node":n["id"],"issue":"screen composition too dense","rule":"hierarchy"})
            for ref in n.get("component_refs",[]):
                if ref not in mapped and ref not in aliases:
                    findings.append({"severity":"blocker","node":n["id"],"issue":f"unmapped component {ref}","rule":"implementation-fidelity"})
    return {"client_id":client_id,"critic":"visual-semantic","findings":findings,"status":"passed" if not any(x["severity"]=="blocker" for x in findings) else "blocked"}
