from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any, Callable
import yaml

ROOT=Path(__file__).resolve().parents[2]
class Phase145Error(RuntimeError): pass

def load(p:Path)->dict[str,Any]:
    if not p.exists(): raise Phase145Error(f"missing:{p}")
    v=yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise Phase145Error(f"invalid-mapping:{p}")
    return v
def any_yaml(p:Path)->bool: return p.exists() and any(p.glob("*.yaml"))
def passed_doc(p:Path, key:str="status", allowed:set[str]|None=None)->bool:
    try: v=load(p)
    except Phase145Error: return False
    allowed=allowed or {"ready","passed","approved","complete","completed","evaluated","resolved","generated","review-ready"}
    return str(v.get(key,"")).lower() in allowed

def assess(client:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client
    def ex(rel:str)->bool: return (p/rel).exists()
    def y(rel:str)->dict[str,Any]:
        try:return load(p/rel)
        except Phase145Error:return {}
    refs=y("experience/references/adaptation.yaml")
    ref_ok=bool(refs.get("sources")) and all(s.get("patterns") and all(not str(x.get("id","")).endswith("pending-analysis") and x.get("decision") in {"REUSE","ADAPT","COMBINE","MODERNIZE","REJECT","BUILD_NEW"} for x in s.get("patterns",[])) for s in refs.get("sources",[]))
    graph=y("derived/journey-graph.yaml")
    journey_ok=bool(graph.get("journeys")) and all(j.get("nodes") and all(n.get("success_state") and n.get("error_state") and "next" in n for n in j.get("nodes",[])) for j in graph.get("journeys",[]))
    design_ir=y("experience/design/design-ir.yaml")
    component=y("experience/design/component-contract-registry.yaml")
    design_ok=bool(design_ir.get("journeys")) and bool(component.get("components"))
    review_pkgs=list((p/"experience"/"review").glob("DRP-*.yaml")) if (p/"experience"/"review").exists() else []
    package=load(review_pkgs[-1]) if review_pkgs else {}
    package_ok=bool(package.get("penpot_ref")) and package.get("status") in {"review-ready","approved"}
    critics={k:y(f"experience/qa/{k}-critic.yaml").get("status")=="passed" for k in ("design","journey")}
    visual_ok=any_yaml(p/"experience"/"visual-qa")
    rounds=list((p/"feedback"/"rounds").glob("*.yaml")) if (p/"feedback"/"rounds").exists() else []
    round_docs=[load(x) for x in rounds]
    approved_round=next((r for r in reversed(round_docs) if r.get("outcome")=="approved"),None)
    feedback_ok=any_yaml(p/"feedback") or bool(rounds)
    approval=y("approved/experience-approval.yaml")
    approval_ok=approval.get("decision")=="approved" and approval.get("immutable") is True
    scope_ok=ex("approved/current-scope.yaml") and any_yaml(p/"approved"/"scope-baselines")
    directions=all(ex(f"experience/directions/{d}.yaml") for d in ("a","b","c"))
    checks=[
      (1,ex("input/client-input.yaml"),"client input"),(2,ex("derived/truth-register.yaml"),"normalized truth"),(3,ex("derived/truth-register.yaml"),"client truth"),
      (4,ex("derived/industry-profile.yaml"),"industry/archetype"),(5,ex("derived/capability-discovery.yaml"),"capability discovery"),(6,ex("derived/benchmark-report.yaml"),"best-practice benchmark"),
      (7,ex("derived/capability-gap-analysis.yaml"),"capability gap"),(8,ex("derived/reuse-decisions.yaml") and ex("derived/capability-discovery.yaml"),"reuse decision"),
      (9,ex("derived/capability-map.yaml"),"capability map"),(10,journey_ok,"detailed executable journey graph"),(11,ex("derived/entity-map.yaml") and ex("contracts/data-contract.yaml"),"entity/data ownership"),
      (12,ex("derived/surface-map.yaml"),"surface map"),(13,ex("derived/integration-map.yaml"),"integration map"),(14,ex("solution/solution-contract.yaml") and any_yaml(p/"solution"/"decisions"),"solution architecture"),
      (15,ref_ok,"reference patterns extracted"),(16,ref_ok,"every reference pattern explicitly decided"),(17,ex("experience/strategy.yaml"),"experience strategy"),(18,directions,"A/B/C directions"),
      (19,ex("experience/design/selection.yaml"),"direction/design selection"),(20,ex("contracts/design-contract.yaml") or ex("experience/design/theme-resolution.yaml"),"design system"),
      (21,bool(component.get("components")),"component contracts"),(22,design_ok,"implementation-aware Design IR"),(23,ex("experience/design/asset-plan.yaml") and ex("experience/design/selection.yaml"),"icons/imagery/motion plan"),
      (24,package_ok,"Penpot-backed design revision"),(25,design_ok,"screen composition represented in Design IR"),(26,all(n.get("state_refs") for j in design_ir.get("journeys",[]) for n in j.get("nodes",[])) if design_ir.get("journeys") else False,"state design"),
      (27,visual_ok,"responsive evidence"),(28,ex("experience/prototypes") and any_yaml(p/"experience"/"prototypes"),"interactive prototype evidence"),
      (29,visual_ok,"automated design QA"),(30,critics["design"],"independent design critic"),(31,critics["journey"],"independent journey critic"),(32,visual_ok,"visual QA"),
      (33,package_ok,"human review package"),(34,package_ok and any(s.get("id")=="overview" for s in package.get("sections",[])),"experience overview"),
      (35,package_ok and any(s.get("id")=="directions" for s in package.get("sections",[])),"A/B/C review"),(36,package_ok and any(s.get("id")=="design-system" for s in package.get("sections",[])),"design-system review"),
      (37,package_ok and any(s.get("id")=="screens" for s in package.get("sections",[])),"screen review"),(38,package_ok and any(s.get("id")=="journeys" for s in package.get("sections",[])),"journey review"),
      (39,package_ok and all(any(s.get("id")==x for s in package.get("sections",[])) for x in ("responsive","states")),"responsive/state review"),
      (40,package_ok and any(s.get("id")=="references" for s in package.get("sections",[])),"reference review"),(41,feedback_ok,"reviewer feedback channel/evidence"),
      (42,approved_round is not None,"human experience decision"),(43,ex("changes") or feedback_ok,"change loop"),(44,approved_round is not None and bool(approved_round.get("qa_refs")),"re-QA after review"),
      (45,approval_ok and scope_ok,"immutable experience approval and scope baseline")
    ]
    rows=[{"step":n,"passed":ok,"evidence":desc} for n,ok,desc in checks]
    return {"client_id":client,"passed":sum(1 for x in rows if x["passed"]),"total":45,"steps":rows,"status":"complete" if all(x["passed"] for x in rows) else "blocked","blockers":[x["step"] for x in rows if not x["passed"]]}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--client",required=True);ap.add_argument("--root",type=Path,default=ROOT);ap.add_argument("--check",action="store_true");a=ap.parse_args()
    r=assess(a.client,a.root);print(yaml.safe_dump(r,sort_keys=False));return 0 if r["status"]=="complete" else 2
if __name__=="__main__": raise SystemExit(main())
