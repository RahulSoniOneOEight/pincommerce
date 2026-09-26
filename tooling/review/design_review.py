from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml
from tooling.contracts.validator import validate_document

ROOT=Path(__file__).resolve().parents[2]
class DesignReviewError(RuntimeError): pass

def load(path:Path)->dict[str,Any]:
    if not path.exists(): raise DesignReviewError(f"Missing required review evidence: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise DesignReviewError(f"Expected mapping: {path}")
    return value

def build_package(client:str, *, design_revision:str, source_revision:str, penpot_ref:str, root:Path=ROOT)->dict[str,Any]:
    if not penpot_ref.strip(): raise DesignReviewError("penpot_ref is required for design review")
    p=root/"client-projects"/client
    graph=load(p/"derived"/"journey-graph.yaml")
    surfaces=load(p/"derived"/"surface-map.yaml").get("required",[])
    adaptation=load(p/"experience"/"references"/"adaptation.yaml")
    unresolved=[x for s in adaptation.get("sources",[]) for x in s.get("patterns",[]) if x.get("id","").endswith("pending-analysis")]
    if unresolved: raise DesignReviewError("Reference adaptation still contains pending-analysis patterns")
    for rel in ["experience/strategy.yaml","experience/design/component-contract-registry.yaml","experience/design/design-ir.yaml"]:
        load(p/rel)
    qa_dir=p/"experience"/"visual-qa"
    qa_refs=[f"experience/visual-qa/{x.name}" for x in sorted(qa_dir.glob("*.yaml"))] if qa_dir.exists() else []
    if not qa_refs: raise DesignReviewError("At least one Visual QA artifact is required")
    sections=[
      ("overview",["experience/strategy.yaml"]),
      ("directions",["experience/directions"]),
      ("design-system",["experience/design/theme-resolution.yaml","experience/design/component-contract-registry.yaml"]),
      ("screens",["experience/design/design-ir.yaml"]),
      ("journeys",["derived/journey-graph.yaml"]),
      ("responsive",qa_refs),("states",["experience/design/design-ir.yaml"]),
      ("references",["experience/references/adaptation.yaml"]),("qa",qa_refs),
      ("feedback",["feedback"]),("approval",["feedback"])
    ]
    doc={"package_id":f"DRP-{client}-{design_revision}","client_id":client,"design_revision":design_revision,"source_revision":source_revision,"penpot_ref":penpot_ref,
         "sections":[{"id":i,"title":i.replace("-"," ").title(),"evidence_refs":r} for i,r in sections],
         "surface_refs":list(surfaces),"journey_refs":[j["id"] for j in graph.get("journeys",[])],"qa_refs":qa_refs,"status":"review-ready"}
    errors=validate_document(doc,"design-review-package")
    if errors: raise DesignReviewError("; ".join(errors))
    return doc

def approve(client:str, *, package_file:str, prototype_revision_ref:str, review_round_ref:str, approved_by:str, approved_at:str, root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client
    package=load(p/"experience"/"review"/package_file)
    round_doc=load(p/review_round_ref)
    if round_doc.get("outcome")!="approved": raise DesignReviewError("Review Round must be approved")
    if any(x.get("status")!="approved" for x in round_doc.get("surface_decisions",[])): raise DesignReviewError("All surfaces must be approved")
    if any(x.get("status")!="approved" for x in round_doc.get("journey_decisions",[])): raise DesignReviewError("All journeys must be approved")
    doc={"approval_id":f"EXP-{client}-{package['design_revision']}","client_id":client,"review_package_ref":f"experience/review/{package_file}",
         "design_revision":package["design_revision"],"source_revision":package["source_revision"],"prototype_revision_ref":prototype_revision_ref,"review_round_ref":review_round_ref,
         "surface_decisions":round_doc["surface_decisions"],"journey_decisions":round_doc["journey_decisions"],"decision":"approved","approved_by":approved_by,"approved_at":approved_at,"immutable":True}
    errors=validate_document(doc,"experience-approval")
    if errors: raise DesignReviewError("; ".join(errors))
    return doc

def main()->int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    b=sub.add_parser("package"); b.add_argument("--client",required=True); b.add_argument("--design-revision",required=True); b.add_argument("--source-revision",required=True); b.add_argument("--penpot-ref",required=True)
    a=sub.add_parser("approve"); a.add_argument("--client",required=True); a.add_argument("--package",required=True); a.add_argument("--prototype-revision-ref",required=True); a.add_argument("--review-round-ref",required=True); a.add_argument("--approved-by",required=True); a.add_argument("--approved-at",required=True)
    x=ap.parse_args()
    try:
      p=ROOT/"client-projects"/x.client
      if x.cmd=="package":
        d=build_package(x.client,design_revision=x.design_revision,source_revision=x.source_revision,penpot_ref=x.penpot_ref); out=p/"experience"/"review"/f"{d['package_id']}.yaml"
      else:
        d=approve(x.client,package_file=x.package,prototype_revision_ref=x.prototype_revision_ref,review_round_ref=x.review_round_ref,approved_by=x.approved_by,approved_at=x.approved_at); out=p/"approved"/"experience-approval.yaml"
      if out.exists(): raise DesignReviewError(f"Refusing to overwrite immutable/review artifact: {out}")
      out.parent.mkdir(parents=True,exist_ok=True); out.write_text(yaml.safe_dump(d,sort_keys=False),encoding="utf-8"); print(out.relative_to(ROOT)); return 0
    except DesignReviewError as e: print(f"design-review-error: {e}"); return 2
if __name__=="__main__": raise SystemExit(main())
