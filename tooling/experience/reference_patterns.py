from __future__ import annotations
from typing import Any

DECISIONS={"REUSE","ADAPT","COMBINE","MODERNIZE","REJECT","BUILD_NEW"}

class ReferencePatternError(RuntimeError): pass

def extract_patterns(record:dict[str,Any])->list[dict[str,Any]]:
    """Extract only patterns actually present in a normalized source record. Never invent patterns."""
    patterns=[]
    for i,p in enumerate(record.get("patterns",[]) or [],1):
        if isinstance(p,str): patterns.append({"id":f"pattern-{i}","name":p,"kind":"declared-pattern","evidence":p})
        elif isinstance(p,dict):
            name=str(p.get("name") or p.get("id") or f"pattern-{i}")
            patterns.append({"id":str(p.get("id") or f"pattern-{i}"),"name":name,"kind":str(p.get("kind") or "declared-pattern"),"evidence":str(p.get("evidence") or name)})
    for i,c in enumerate(record.get("components",[]) or [],1):
        if isinstance(c,str): name=c
        elif isinstance(c,dict): name=str(c.get("name") or c.get("id") or f"component-{i}")
        else: continue
        patterns.append({"id":f"component-{i}","name":name,"kind":"component","evidence":name})
    return patterns

def decide_patterns(source:dict[str,Any], *, journey_ids:list[str], surfaces:list[str], decisions:dict[str,str]|None=None)->dict[str,Any]:
    extracted=extract_patterns(source)
    if not extracted:
        raise ReferencePatternError(f"No extracted patterns for source {source.get('source_id')}; source analysis is incomplete")
    decisions=decisions or {}
    out=[]
    for p in extracted:
        decision=decisions.get(p["id"])
        if decision not in DECISIONS:
            raise ReferencePatternError(f"Pattern {p['id']} requires explicit decision")
        out.append({**p,"decision":decision,"journeys":journey_ids,"surfaces":surfaces})
    return {"source_id":source["source_id"],"ref":source.get("source_ref") or source.get("provenance",{}).get("source_ref"),"patterns":out}
