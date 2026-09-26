from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[2]

class DirectionSynthesisError(RuntimeError): pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise DirectionSynthesisError(f"Missing direction input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise DirectionSynthesisError(f"Expected mapping: {path}")
    return value

def build(client_id:str,root:Path=ROOT)->dict[str,dict[str,Any]]:
    p=root/"client-projects"/client_id
    strategy=_load(p/"experience"/"synthesis.yaml")
    graph=_load(p/"derived"/"journey-graph.yaml")
    refs=_load(p/"experience"/"references"/"adaptation.yaml")
    surfaces=sorted({s for j in graph.get("journeys",[]) for s in j.get("surfaces",[])})
    journeys=[j["id"] for j in graph.get("journeys",[])]
    patterns=[p for s in refs.get("sources",[]) for p in s.get("patterns",[]) if p.get("decision") in {"REUSE","ADAPT","COMBINE","MODERNIZE"}]
    configs={
      "A":{"strategy":"conversion-first","density":"balanced","navigation":"guided","merchandising":"transactional","motion":"restrained"},
      "B":{"strategy":"utility-first","density":"compact","navigation":"task-oriented","merchandising":"information-dense","motion":"minimal"},
      "C":{"strategy":"brand-and-discovery-first","density":"editorial","navigation":"exploratory","merchandising":"visual-storytelling","motion":"expressive-controlled"},
    }
    out={}
    for key,cfg in configs.items():
        picks=[x for i,x in enumerate(patterns) if i%3=="ABC".index(key)] or patterns[:2]
        out[key]={
            "direction_id":f"DIR-{client_id.upper()}-{key}",
            "client_id":client_id,
            "strategy":cfg["strategy"],
            "surfaces":surfaces,
            "journey_emphasis":journeys,
            "design_intent":{
                "density":cfg["density"],"navigation":cfg["navigation"],"merchandising":cfg["merchandising"],
                "motion":cfg["motion"],"responsive":"platform-specific-semantic-parity",
                "states":["default","loading","empty","error","success","disabled"],
            },
            "reference_pattern_refs":[f"{x.get('id')}" for x in picks],
            "differentiators":[cfg["navigation"],cfg["merchandising"],cfg["motion"]],
            "strategy_principles":strategy.get("principles",[]),
            "status":"review-ready",
        }
    return out
