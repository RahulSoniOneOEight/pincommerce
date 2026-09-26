from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from tooling.contracts.validator import validate_document

ROOT=Path(__file__).resolve().parents[2]

class AssetIntelligenceError(RuntimeError): pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise AssetIntelligenceError(f"Missing asset input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise AssetIntelligenceError(f"Expected mapping: {path}")
    return value

def build(client_id:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    inventory=_load(p/"experience"/"design"/"source-inventory.yaml")
    graph=_load(p/"derived"/"journey-graph.yaml")
    requests=[]
    seen=set()
    for src in inventory.get("sources",[]):
        for asset in src.get("assets",[]) or []:
            ref=str(asset.get("ref") if isinstance(asset,dict) else asset)
            if not ref or ref in seen: continue
            seen.add(ref)
            requests.append({
                "id":f"asset-{len(requests)+1}",
                "purpose":str(asset.get("purpose","reference-or-client-media") if isinstance(asset,dict) else "reference-or-client-media"),
                "provider_policy":"client-owned-or-approved-open-source-first",
                "query":{"source_id":src.get("id"),"ref":ref},
                "selected_asset":{"ref":ref,"provenance":src.get("ref"),"license":asset.get("license") if isinstance(asset,dict) else None},
                "status":"selected",
            })
    if not requests:
        for j in graph.get("journeys",[]):
            requests.append({
                "id":f"journey-{j['id']}-hero",
                "purpose":f"journey imagery for {j['id']}",
                "provider_policy":"client-owned-or-approved-open-source-first",
                "query":{"journey":j["id"],"surfaces":j.get("surfaces",[])},
                "selected_asset":None,
                "status":"planned",
            })
    plan={"asset_plan_id":f"ASSET-{client_id}","client_id":client_id,"source_order":["client-media","approved-reference","approved-open-source","generated-if-authorized"],"requests":requests,"status":"ready"}
    errors=validate_document(plan,"asset-selection")
    if errors: raise AssetIntelligenceError("; ".join(errors))
    return plan
