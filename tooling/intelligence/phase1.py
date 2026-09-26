from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml
from tooling.contracts.validator import validate_document
from tooling.validation.identifiers import validate_identifier, IdentifierError

ROOT=Path(__file__).resolve().parents[2]

class IntelligenceError(RuntimeError): pass

def load(path: Path)->dict[str,Any]:
    if not path.exists(): raise IntelligenceError(f"Missing required artifact: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise IntelligenceError(f"Expected mapping in {path}")
    return value

def _actor(journey_id:str)->str:
    if any(x in journey_id for x in ("quote","credit","repeat")): return "b2b-buyer"
    if "seller" in journey_id: return "seller"
    return "customer"

def build_journey_graph(client_id:str, root:Path=ROOT)->dict[str,Any]:
    project=root/"client-projects"/client_id
    journey_map=load(project/"derived"/"journey-map.yaml")
    surfaces=load(project/"derived"/"surface-map.yaml").get("required",[])
    capabilities=load(project/"derived"/"capability-map.yaml")
    capset=set(sum((capabilities.get(k,[]) or [] for k in ("mandatory","core","recommended","requested_additional")),[]))
    preferred_surface="customer-app" if "customer-app" in surfaces else (surfaces[0] if surfaces else "web-store")
    templates={
      "browse-to-buy":[("discover","catalogue"),("select","catalogue"),("cart","cart"),("checkout","checkout"),("confirm","orders")],
      "search-to-buy":[("search","search"),("select","catalogue"),("cart","cart"),("checkout","checkout"),("confirm","orders")],
      "order-tracking":[("open-order","orders"),("track","fulfilment")],
      "return-refund":[("open-order","orders"),("request-return","return-refund"),("track-refund","return-refund")],
      "quote-to-order":[("create-rfq","quote-rfq"),("review-quote","quote-rfq"),("accept","orders")],
      "repeat-order":[("open-history","orders"),("reorder","reorder"),("checkout","checkout")],
      "credit-order":[("select-credit","credit-management"),("approve","approval-workflow"),("confirm","orders")],
    }
    journeys=[]
    for item in journey_map.get("journeys",[]):
        jid=item["id"]; steps=templates.get(jid,[(jid,jid if jid in capset else "orders")])
        nodes=[]
        for i,(action,cap) in enumerate(steps):
            nodes.append({"id":f"{jid}.{i+1}","action":action,"surface":preferred_surface,"capability":cap,
              "success_state":f"{action}-complete","error_state":f"{action}-failed","empty_state":f"{action}-empty",
              "permission":_actor(jid),"event":f"{jid}.{action}.completed","next":[f"{jid}.{i+2}"] if i+1<len(steps) else []})
        journeys.append({"id":jid,"actor":_actor(jid),"surfaces":[preferred_surface],"nodes":nodes})
    doc={"client_id":client_id,"journeys":journeys,"status":"generated"}
    errors=validate_document(doc,"journey-graph")
    if errors: raise IntelligenceError("; ".join(errors))
    return doc

def build_reference_adaptation(client_id:str, root:Path=ROOT)->dict[str,Any]:
    project=root/"client-projects"/client_id
    inventory=load(project/"experience"/"design"/"source-inventory.yaml")
    graph=load(project/"derived"/"journey-graph.yaml")
    journey_ids=[x["id"] for x in graph.get("journeys",[])]
    sources=[]
    for source in inventory.get("sources",[]):
        # No silent non-use: unknown/unanalysed sources are explicitly blocked as BUILD_NEW pending extraction.
        patterns=[{"id":f"{source['id']}-pending-analysis","decision":"BUILD_NEW",
          "reason":"No extracted reusable pattern is recorded yet; explicit analysis is required before this source can influence implementation.",
          "journeys":journey_ids,"surfaces":[],"implementation_target":None}]
        sources.append({"source_id":source["id"],"ref":source["ref"],"patterns":patterns})
    doc={"client_id":client_id,"sources":sources,"status":"evaluated"}
    errors=validate_document(doc,"reference-adaptation")
    if errors: raise IntelligenceError("; ".join(errors))
    return doc

def build_journey_capability_map(client_id:str, root:Path=ROOT)->dict[str,Any]:
    project=root/"client-projects"/client_id
    graph=load(project/"derived"/"journey-graph.yaml")
    discovery=load(project/"derived"/"capability-discovery.yaml")
    index={}
    for d in discovery.get("discovered",[]):
        for cap in d.get("matched_capabilities",[]):
            index[cap]=d
    mappings=[]; gaps=[]
    for journey in graph.get("journeys",[]):
        for node in journey.get("nodes",[]):
            cap=node.get("capability")
            if not cap: continue
            found=index.get(cap)
            if found:
                mappings.append({"journey":journey["id"],"node":node["id"],"capability":cap,
                  "domain":found.get("domain"),"runtime":found.get("runtime"),"classification":found.get("classification","RETAIN")})
            else:
                gaps.append({"journey":journey["id"],"node":node["id"],"capability":cap,"reason":"not mapped to discovered platform capability"})
    doc={"client_id":client_id,"mappings":mappings,"gaps":gaps,"status":"complete" if not gaps else "gaps-present"}
    errors=validate_document(doc,"journey-capability-map")
    if errors: raise IntelligenceError("; ".join(errors))
    return doc

def generate(client_id:str,root:Path=ROOT,overwrite:bool=False)->list[Path]:
    try: validate_identifier(client_id,kind="client_id")
    except IdentifierError as exc: raise IntelligenceError(str(exc)) from exc
    project=root/"client-projects"/client_id
    outputs=[("derived/journey-graph.yaml",build_journey_graph(client_id,root)),
             ("experience/references/adaptation.yaml",None),
             ("derived/journey-capability-map.yaml",None)]
    written=[]
    # Write in dependency order so later builders consume the generated artifacts.
    p=project/outputs[0][0]
    if p.exists() and not overwrite: raise IntelligenceError(f"Refusing to overwrite: {p}")
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(yaml.safe_dump(outputs[0][1],sort_keys=False),encoding="utf-8"); written.append(p)
    for rel,builder in [(outputs[1][0],build_reference_adaptation),(outputs[2][0],build_journey_capability_map)]:
        p=project/rel
        if p.exists() and not overwrite: raise IntelligenceError(f"Refusing to overwrite: {p}")
        doc=builder(client_id,root); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(yaml.safe_dump(doc,sort_keys=False),encoding="utf-8"); written.append(p)
    mapped=load(project/"derived"/"journey-capability-map.yaml")
    gap_path=project/"derived"/"implementation-gap.yaml"
    if gap_path.exists() and not overwrite: raise IntelligenceError(f"Refusing to overwrite: {gap_path}")
    gap_doc={"client_id":client_id,"gaps":mapped.get("gaps",[]),"status":"clear" if not mapped.get("gaps") else "action-required"}
    gap_path.write_text(yaml.safe_dump(gap_doc,sort_keys=False),encoding="utf-8"); written.append(gap_path)
    return written

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--client",required=True); ap.add_argument("--root",type=Path,default=ROOT); ap.add_argument("--overwrite",action="store_true")
    args=ap.parse_args()
    try:
        for p in generate(args.client,args.root,args.overwrite): print(p.relative_to(args.root))
        return 0
    except IntelligenceError as exc:
        print(f"phase1-intelligence-error: {exc}"); return 2
if __name__=="__main__": raise SystemExit(main())
