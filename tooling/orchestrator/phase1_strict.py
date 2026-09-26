from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml

from tooling.intelligence.journey_engine import build as build_journeys, validate_executable
from tooling.experience.reference_engine import analyze as analyze_references, apply_decisions
from tooling.experience.synthesis import synthesize
from tooling.experience.critics import design_critic, journey_critic, reference_critic
from tooling.experience.penpot_bridge import build_manifest, verify_manifest, PenpotBridgeError

ROOT=Path(__file__).resolve().parents[2]

class StrictPhase1Error(RuntimeError):
    pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise StrictPhase1Error(f"Missing strict Phase1 input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise StrictPhase1Error(f"Expected mapping: {path}")
    return value

def _write(path:Path,value:dict[str,Any],overwrite:bool)->None:
    if path.exists() and not overwrite: raise StrictPhase1Error(f"Refusing to overwrite: {path}")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(value,sort_keys=False),encoding="utf-8")

def generate(client_id:str, *, root:Path=ROOT, overwrite:bool=False, penpot_project:str|None=None, penpot_revision:str|None=None)->dict[str,Any]:
    p=root/"client-projects"/client_id
    graph=build_journeys(client_id,root)
    errors=validate_executable(graph)
    if errors: raise StrictPhase1Error("Journey graph is not executable: "+"; ".join(errors))
    _write(p/"derived"/"journey-graph.yaml",graph,overwrite)

    analysis=analyze_references(client_id,root)
    decisions_path=p/"experience"/"references"/"decisions.yaml"
    decisions=_load(decisions_path) if decisions_path.exists() else {}
    adaptation=apply_decisions(analysis,decisions.get("sources",decisions))
    if adaptation.get("blockers"):
        _write(p/"experience"/"references"/"analysis.yaml",analysis,overwrite)
        raise StrictPhase1Error("Reference intelligence blocked: "+", ".join(x["reason"] for x in adaptation["blockers"]))
    adaptation.pop("blockers",None)
    _write(p/"experience"/"references"/"adaptation.yaml",adaptation,overwrite)

    strategy=synthesize(client_id,root)
    _write(p/"experience"/"synthesis.yaml",strategy,overwrite)

    critics={
        "reference":reference_critic(client_id,root),
        "journey":journey_critic(client_id,root),
    }
    for name,value in critics.items():
        _write(p/"experience"/"qa"/f"{name}-critic-v2.yaml",value,overwrite)
        if value["status"]!="passed": raise StrictPhase1Error(f"{name} critic blocked")

    penpot=None
    if penpot_project or penpot_revision:
        if not penpot_project or not penpot_revision: raise StrictPhase1Error("Both penpot_project and penpot_revision are required")
        penpot=build_manifest(client_id,project_ref=penpot_project,revision_ref=penpot_revision,root=root)
        _write(p/"experience"/"design"/"penpot-manifest.yaml",penpot,overwrite)

    return {"client_id":client_id,"journeys":"passed","references":"passed","synthesis":"passed","critics":{k:v["status"] for k,v in critics.items()},"penpot":"manifest-created" if penpot else "external-evidence-required","status":"ready-for-design" if penpot else "blocked-on-penpot"}

def check(client_id:str, root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    blockers=[]
    try:
        graph=_load(p/"derived"/"journey-graph.yaml"); blockers += validate_executable(graph)
    except StrictPhase1Error as exc: blockers.append(str(exc))
    try:
        refs=_load(p/"experience"/"references"/"adaptation.yaml")
        for source in refs.get("sources",[]):
            if not source.get("patterns"): blockers.append(f"{source.get('source_id')}: no reference patterns")
            for pattern in source.get("patterns",[]):
                if pattern.get("decision") not in {"REUSE","ADAPT","COMBINE","MODERNIZE","REJECT","BUILD_NEW"}: blockers.append(f"{pattern.get('id')}: missing decision")
    except StrictPhase1Error as exc: blockers.append(str(exc))
    manifest=p/"experience"/"design"/"penpot-manifest.yaml"
    observed=p/"experience"/"design"/"penpot-observed.yaml"
    if not manifest.exists() or not observed.exists():
        blockers.append("real Penpot manifest/observed evidence missing")
    else:
        blockers += verify_manifest(_load(manifest),_load(observed))
    try:
        for critic in ("design","journey","reference"):
            candidate=p/"experience"/"qa"/f"{critic}-critic-v2.yaml"
            if not candidate.exists() and critic=="design": candidate=p/"experience"/"qa"/"design-critic.yaml"
            if _load(candidate).get("status")!="passed": blockers.append(f"{critic} critic not passed")
    except StrictPhase1Error as exc: blockers.append(str(exc))
    return {"client_id":client_id,"status":"passed" if not blockers else "blocked","blockers":blockers}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--client",required=True);ap.add_argument("--root",type=Path,default=ROOT);ap.add_argument("--overwrite",action="store_true");ap.add_argument("--check",action="store_true");ap.add_argument("--penpot-project");ap.add_argument("--penpot-revision")
    a=ap.parse_args()
    try:
        value=check(a.client,a.root) if a.check else generate(a.client,root=a.root,overwrite=a.overwrite,penpot_project=a.penpot_project,penpot_revision=a.penpot_revision)
        print(yaml.safe_dump(value,sort_keys=False));return 0 if value["status"] in {"passed","ready-for-design","blocked-on-penpot"} else 2
    except (StrictPhase1Error,PenpotBridgeError) as exc:
        print(f"phase1-strict-error: {exc}");return 2
if __name__=="__main__": raise SystemExit(main())
