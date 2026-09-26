from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml

from tooling.intelligence.best_practice_engine import build as build_best_practice
from tooling.experience.deep_reference import analyze_client as analyze_references
from tooling.experience.direction_synthesis import build as build_directions
from tooling.experience.asset_intelligence import build as build_assets
from tooling.experience.visual_critic import evaluate as visual_critic

ROOT=Path(__file__).resolve().parents[2]

class FinalGapError(RuntimeError): pass

def _write(path:Path,value:dict[str,Any],overwrite:bool)->None:
    if path.exists() and not overwrite: raise FinalGapError(f"Refusing to overwrite: {path}")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(value,sort_keys=False),encoding="utf-8")

def run(client_id:str,root:Path=ROOT,overwrite:bool=False)->dict[str,Any]:
    p=root/"client-projects"/client_id
    outputs={}
    best=build_best_practice(client_id,root); outputs["best_practice"]=best
    _write(p/"derived"/"best-practice-intelligence.yaml",best,overwrite)

    refs=analyze_references(client_id,root); outputs["deep_reference"]=refs
    _write(p/"experience"/"references"/"deep-analysis.yaml",refs,overwrite)

    directions=build_directions(client_id,root); outputs["directions"]=directions
    for key,doc in directions.items():
        _write(p/"experience"/"directions"/f"{key.lower()}.yaml",doc,overwrite)

    assets=build_assets(client_id,root); outputs["assets"]=assets
    _write(p/"experience"/"design"/"asset-plan.yaml",assets,overwrite)

    critic=visual_critic(client_id,root); outputs["visual_critic"]=critic
    _write(p/"experience"/"qa"/"visual-semantic-critic.yaml",critic,overwrite)

    blockers=[]
    if best["status"]!="evidence-backed": blockers.append("best-practice research lacks evidence for one or more capabilities")
    if refs["status"]!="ready": blockers.append("one or more reference sources lack extractable evidence")
    if critic["status"]!="passed": blockers.append("visual semantic critic blocked")
    return {"client_id":client_id,"status":"ready" if not blockers else "blocked","blockers":blockers,"outputs":list(outputs)}

def main()->int:
    ap=argparse.ArgumentParser(description="Close remaining Phase 1 intelligence/design gaps")
    ap.add_argument("--client",required=True);ap.add_argument("--root",type=Path,default=ROOT);ap.add_argument("--overwrite",action="store_true")
    a=ap.parse_args()
    try:
        result=run(a.client,a.root,a.overwrite);print(yaml.safe_dump(result,sort_keys=False));return 0 if result["status"]=="ready" else 2
    except Exception as exc:
        print(f"phase1-final-gap-error: {exc}");return 2

if __name__=="__main__": raise SystemExit(main())
