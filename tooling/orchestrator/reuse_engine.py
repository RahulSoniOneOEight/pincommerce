from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[2]

class ReuseEngineError(RuntimeError):
    pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise ReuseEngineError(f"Missing reuse input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ReuseEngineError(f"Expected mapping: {path}")
    return value

def _tokens(value:str)->set[str]:
    return {x for x in re.split(r"[^a-z0-9]+",value.lower()) if len(x)>1}

def _score(a:str,b:str)->float:
    aa,bb=_tokens(a),_tokens(b)
    return len(aa&bb)/len(aa|bb) if aa|bb else 0.0

def decide(client_id:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    capability=_load(p/"derived"/"capability-map.yaml")
    discovery=_load(p/"derived"/"capability-discovery.yaml")
    required=[]
    for key in ("mandatory","core","recommended","requested_additional"):
        required.extend(capability.get(key,[]) or [])
    pool=[]
    for item in discovery.get("discovered",[]):
        names=list(item.get("matched_capabilities",[]) or [])
        for name in names:
            pool.append({"capability":name,"domain":item.get("domain"),"runtime":item.get("runtime"),"classification":item.get("classification","RETAIN"),"evidence":item.get("evidence_ref") or item.get("path")})
    decisions=[]
    for req in dict.fromkeys(required):
        ranked=sorted(({**x,"score":_score(req,x["capability"])} for x in pool),key=lambda x:x["score"],reverse=True)
        best=ranked[0] if ranked else None
        if best and best["score"]>=0.75: action="REUSE"
        elif best and best["score"]>=0.4: action="ADAPT"
        else: action="BUILD_NEW"
        decisions.append({"requested":req,"decision":action,"match":best,"alternatives":ranked[1:4]})
    return {"client_id":client_id,"decisions":decisions,"status":"evaluated"}
