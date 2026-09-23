from __future__ import annotations
from pathlib import Path
from typing import Any
import argparse,yaml
from tooling.experience.component_lifecycle import transition
ROOT=Path(__file__).resolve().parents[2]
REGISTRY=ROOT/"design-intelligence"/"component-registry.yaml"

def load_registry(path: Path=REGISTRY)->dict[str,Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def records(doc: dict[str,Any])->dict[str,Any]:
    return doc.setdefault("lifecycle_records",{})

def apply(component_id: str,target: str,*,evidence:list[str],approver:str|None,path:Path=REGISTRY)->dict[str,Any]:
    doc=load_registry(path); items=records(doc)
    if component_id not in items: raise ValueError(f"Unknown component: {component_id}")
    items[component_id]=transition(items[component_id],target,evidence=evidence,approver=approver)
    path.write_text(yaml.safe_dump(doc,sort_keys=False),encoding="utf-8")
    return items[component_id]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("component_id"); p.add_argument("target",choices=["evaluated","approved","deprecated"])
    p.add_argument("--evidence",action="append",required=True); p.add_argument("--approver")
    a=p.parse_args(); result=apply(a.component_id,a.target,evidence=a.evidence,approver=a.approver)
    print(yaml.safe_dump(result,sort_keys=False)); return 0
if __name__=="__main__": raise SystemExit(main())
