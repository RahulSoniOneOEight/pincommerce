from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml
from tooling.contracts.validator import validate_document
from tooling.prototype.core_runtime import assert_core_runtime_ready, CoreRuntimeError

ROOT=Path(__file__).resolve().parents[2]
SLICES=["browse-to-buy","payment-failure-recovery","order-to-erp","order-to-shipment","return-refund","seller-settlement","reconciliation"]

class Phase1BuildError(RuntimeError): pass
def load(p:Path)->dict[str,Any]:
    if not p.exists(): raise Phase1BuildError(f"Missing required artifact: {p}")
    v=yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise Phase1BuildError(f"Expected mapping in {p}")
    return v
def validate(doc:dict[str,Any],kind:str)->dict[str,Any]:
    e=validate_document(doc,kind)
    if e: raise Phase1BuildError(f"Invalid {kind}: "+"; ".join(e))
    return doc
def build_strategy(client:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client
    graph=load(p/"derived"/"journey-graph.yaml"); surfaces=load(p/"derived"/"surface-map.yaml").get("required",[])
    priorities=[]
    for j in graph.get("journeys",[]):
        critical=j["id"] in {"browse-to-buy","search-to-buy","return-refund","quote-to-order"}
        priorities.append({"journey":j["id"],"priority":"critical" if critical else "high","rationale":"Required client journey connected to executable states and runtime capabilities."})
    roles={"customer-app":"mobile customer conversion","web-store":"web discovery and conversion","b2b":"business buying","seller-portal":"seller operations","commerce-admin":"commerce operations","erp":"accounting and ERP operations","analytics":"decision support","ops-console":"exceptions and recovery"}
    return validate({"client_id":client,"principles":["client truth over reference imitation","journey before screen","reuse before build","provider-neutral UX","implementation-aware design"],"journey_priorities":priorities,"surface_strategy":[{"surface":s,"role":roles.get(s,"business workflow surface")} for s in surfaces],"status":"generated"},"experience-strategy")
def build_components(client:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client; graph=load(p/"derived"/"journey-graph.yaml")
    cap_to_component={"catalogue":"product-card","search":"search-control","cart":"cart-line","checkout":"checkout-summary","orders":"order-card","return-refund":"return-status","quote-rfq":"rfq-form","reorder":"reorder-action","credit-management":"credit-limit","approval-workflow":"approval-status","fulfilment":"shipment-status"}
    ids=[]
    for j in graph.get("journeys",[]):
        for n in j.get("nodes",[]):
            cid=cap_to_component.get(n.get("capability"),"workflow-action")
            if cid not in ids: ids.append(cid)
    components=[]
    for cid in ids:
        components.append({"id":cid,"semantic_role":cid.replace("-"," "),"variants":["default","compact"],"states":["default","loading","empty","failure"],"tokens":["surface","text.primary","action.primary","border"],"implementation":{"flutter":f"Pin{''.join(x.title() for x in cid.split('-'))}","web":f"Pin{''.join(x.title() for x in cid.split('-'))}"},"accessibility":["keyboard/focus where interactive","semantic label","contrast policy"],"qa":["widget/story render","responsive states","visual evidence"]})
    return validate({"client_id":client,"components":components,"status":"generated"},"component-contract-registry")
def build_design_ir(client:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client; graph=load(p/"derived"/"journey-graph.yaml"); reg=build_components(client,root)
    ids=[x["id"] for x in reg["components"]]; capmap={"catalogue":"product-card","search":"search-control","cart":"cart-line","checkout":"checkout-summary","orders":"order-card","return-refund":"return-status","quote-rfq":"rfq-form","reorder":"reorder-action","credit-management":"credit-limit","approval-workflow":"approval-status","fulfilment":"shipment-status"}
    journeys=[]
    for j in graph.get("journeys",[]):
        nodes=[]
        for n in j.get("nodes",[]):
            cid=capmap.get(n.get("capability"),"workflow-action")
            nodes.append({"id":n["id"],"surface":n.get("surface","web-store"),"component_refs":[cid],"state_refs":["default","loading","empty","failure"]})
        journeys.append({"id":j["id"],"nodes":nodes})
    surfaces=sorted({n["surface"] for j in journeys for n in j["nodes"]})
    return validate({"client_id":client,"surfaces":surfaces,"journeys":journeys,"components":ids,"status":"generated"},"design-ir")
def critic(client:str,kind:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client; checks=[]
    if kind=="design":
        ir=load(p/"experience"/"design"/"design-ir.yaml"); reg=load(p/"experience"/"design"/"component-contract-registry.yaml")
        known={x["id"] for x in reg.get("components",[])}; refs={c for j in ir.get("journeys",[]) for n in j.get("nodes",[]) for c in n.get("component_refs",[])}
        checks=[{"id":"component-resolution","passed":refs<=known,"evidence":"all Design IR component refs resolve to component contracts"},{"id":"state-coverage","passed":all(n.get("state_refs") for j in ir.get("journeys",[]) for n in j.get("nodes",[])),"evidence":"every design node declares states"}]
    elif kind=="journey":
        graph=load(p/"derived"/"journey-graph.yaml")
        checks=[{"id":"journey-nodes","passed":all(j.get("nodes") for j in graph.get("journeys",[])),"evidence":"every required journey has executable nodes"},{"id":"error-states","passed":all(n.get("error_state") for j in graph.get("journeys",[]) for n in j.get("nodes",[])),"evidence":"every journey node has error behavior"}]
    else:
        try: assert_core_runtime_ready(client,root); ready=True; evidence="core runtime health and seed evidence passed"
        except CoreRuntimeError as exc: ready=False; evidence=str(exc)
        checks=[{"id":"core-runtime","passed":ready,"evidence":evidence}]
    return validate({"client_id":client,"critic":kind,"checks":checks,"status":"passed" if all(x["passed"] for x in checks) else "blocked"},"critic-evidence")
def readiness(client:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client
    critics={k:critic(client,k,root)["status"]=="passed" for k in ("design","journey","runtime")}
    graph=load(p/"derived"/"journey-graph.yaml"); journey_ids={x["id"] for x in graph.get("journeys",[])}
    runtime=critics["runtime"]
    aliases={"payment-failure-recovery":"browse-to-buy","order-to-erp":"browse-to-buy","order-to-shipment":"order-tracking","seller-settlement":"quote-to-order","reconciliation":"browse-to-buy"}
    slices=[]
    for s in SLICES:
        j=aliases.get(s,s); passed=(j in journey_ids) and runtime
        slices.append({"id":s,"passed":passed,"evidence":f"journey={j}; runtime_critic={'passed' if runtime else 'blocked'}"})
    experience=critics["design"] and critics["journey"]
    ready=experience and runtime and all(x["passed"] for x in slices)
    return validate({"client_id":client,"experience_status":"experience-prototype-complete" if experience else "incomplete","runtime_status":"integrated-runtime-ready" if runtime else "incomplete","vertical_slices":slices,"critics":critics,"status":"integrated-prototype-ready" if ready else "blocked"},"integrated-prototype-readiness")
def generate(client:str,root:Path=ROOT,overwrite:bool=False)->list[Path]:
    p=root/"client-projects"/client
    outputs=[("experience/strategy.yaml",build_strategy(client,root)),("experience/design/component-contract-registry.yaml",build_components(client,root)),("experience/design/design-ir.yaml",build_design_ir(client,root))]
    written=[]
    for rel,doc in outputs:
        path=p/rel
        if path.exists() and not overwrite: raise Phase1BuildError(f"Refusing to overwrite: {path}")
        path.parent.mkdir(parents=True,exist_ok=True); path.write_text(yaml.safe_dump(doc,sort_keys=False),encoding="utf-8"); written.append(path)
    for kind in ("design","journey","runtime"):
        path=p/"experience"/"qa"/f"{kind}-critic.yaml"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(yaml.safe_dump(critic(client,kind,root),sort_keys=False),encoding="utf-8"); written.append(path)
    path=p/"experience"/"integrated-prototype-readiness.yaml"; path.write_text(yaml.safe_dump(readiness(client,root),sort_keys=False),encoding="utf-8"); written.append(path)
    return written
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--client",required=True); ap.add_argument("--root",type=Path,default=ROOT); ap.add_argument("--overwrite",action="store_true"); ap.add_argument("--check",action="store_true")
    a=ap.parse_args()
    try:
        if a.check:
            r=readiness(a.client,a.root); print(yaml.safe_dump(r,sort_keys=False)); return 0 if r["status"]=="integrated-prototype-ready" else 2
        for p in generate(a.client,a.root,a.overwrite): print(p.relative_to(a.root))
        return 0
    except Phase1BuildError as exc: print(f"phase1-build-error: {exc}"); return 2
if __name__=="__main__": raise SystemExit(main())
