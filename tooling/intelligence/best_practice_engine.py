from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[2]

class BestPracticeError(RuntimeError): pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise BestPracticeError(f"Missing best-practice input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise BestPracticeError(f"Expected mapping: {path}")
    return value

def _hash(value:Any)->str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":")).encode()
    return "sha256:"+hashlib.sha256(raw).hexdigest()

def build(client_id:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    industry=_load(p/"derived"/"industry-profile.yaml")
    capability=_load(p/"derived"/"capability-map.yaml")
    truth=_load(p/"derived"/"truth-register.yaml")
    inventory_path=p/"intelligence"/"research"/"sources.yaml"
    inventory=_load(inventory_path) if inventory_path.exists() else {"sources":[]}
    sources=[]
    for src in inventory.get("sources",[]):
        if not src.get("id") or not src.get("ref") or not src.get("captured_at"):
            raise BestPracticeError("Every research source needs id, ref, captured_at")
        sources.append({
            "id":src["id"],"ref":src["ref"],"captured_at":src["captured_at"],
            "publisher":src.get("publisher"),"kind":src.get("kind","research"),
            "evidence":src.get("evidence",[]),"content_hash":src.get("content_hash")
        })
    required=[]
    for key in ("mandatory","core","recommended","requested_additional"):
        required.extend(capability.get(key,[]) or [])
    recommendations=[]
    for cap in dict.fromkeys(required):
        supporting=[s["id"] for s in sources if cap in (s.get("evidence") or [])]
        recommendations.append({
            "capability":cap,
            "recommendation":"retain-or-implement",
            "evidence_refs":supporting,
            "confidence":"high" if supporting else "low",
            "requires_human_review":not bool(supporting),
        })
    result={
        "client_id":client_id,
        "industry":industry.get("industry") or industry.get("archetype"),
        "source_inventory_ref":"intelligence/research/sources.yaml",
        "source_count":len(sources),
        "sources":sources,
        "recommendations":recommendations,
        "truth_hash":_hash(truth),
        "status":"evidence-backed" if sources and all(x["evidence_refs"] for x in recommendations) else "review-required",
    }
    return result
