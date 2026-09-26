from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable
import urllib.request
import yaml

ROOT=Path(__file__).resolve().parents[2]

class PenpotAutomationError(RuntimeError): pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise PenpotAutomationError(f"Missing Penpot input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise PenpotAutomationError(f"Expected mapping: {path}")
    return value

def build_operations(client_id:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    master=_load(p/"experience"/"design"/"master-design-system.yaml")
    registry=_load(p/"experience"/"design"/"ui-implementation-registry.yaml")
    ir=_load(p/"experience"/"design"/"design-ir.yaml")
    graph=_load(p/"derived"/"journey-graph.yaml")
    components=[]
    for item in registry.get("components",[]):
        components.append({"semantic_id":item["semantic_id"],"component":item["penpot"].get("component"),"variants":item["penpot"].get("variants",[])})
    screens=[]
    for journey in ir.get("journeys",[]):
        for node in journey.get("nodes",[]):
            screens.append({"id":node["id"],"surface":node["surface"],"components":node.get("component_refs",[]),"states":node.get("state_refs",[])})
    prototypes=[]
    for journey in graph.get("journeys",[]):
        prototypes.append({"journey":journey["id"],"nodes":[{"id":n["id"],"action":n["action"],"next":n.get("next",[])} for n in journey.get("nodes",[])]})
    return {
        "client_id":client_id,
        "tokens":master.get("tokens",{}),
        "breakpoints":master.get("breakpoints",{}),
        "components":components,
        "screens":screens,
        "interactive_journeys":prototypes,
        "mode":"semantic-design-import",
    }

def push(client_id:str,*,project_id:str,root:Path=ROOT,endpoint:str|None=None,token:str|None=None,opener:Callable[...,Any]=urllib.request.urlopen)->dict[str,Any]:
    endpoint=endpoint or os.getenv("PENPOT_WRITE_URL")
    token=token or os.getenv("PENPOT_TOKEN")
    if not endpoint or not token:
        raise PenpotAutomationError("PENPOT_WRITE_URL and PENPOT_TOKEN are required for real Penpot write execution")
    payload=build_operations(client_id,root)
    payload["project_id"]=project_id
    request=urllib.request.Request(endpoint,data=json.dumps(payload).encode("utf-8"),method="POST",headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"})
    with opener(request,timeout=60) as response:
        result=json.loads(response.read().decode("utf-8"))
    if not isinstance(result,dict) or not result.get("revision_ref"):
        raise PenpotAutomationError("Penpot bridge response must contain revision_ref")
    return {"project_ref":project_id,"revision_ref":result["revision_ref"],"components":result.get("components",[]),"interactive_journeys":result.get("interactive_journeys",[]),"status":"written"}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--client",required=True);ap.add_argument("--project");ap.add_argument("--root",type=Path,default=ROOT);ap.add_argument("--push",action="store_true")
    a=ap.parse_args()
    try:
        value=push(a.client,project_id=a.project,root=a.root) if a.push else build_operations(a.client,a.root)
        print(yaml.safe_dump(value,sort_keys=False));return 0
    except PenpotAutomationError as exc:
        print(f"penpot-automation-error: {exc}");return 2

if __name__=="__main__": raise SystemExit(main())
