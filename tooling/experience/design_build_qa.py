from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml

from tooling.contracts.validator import validate_document
from tooling.experience.ui_resolver import resolve_component, ResolverError

ROOT = Path(__file__).resolve().parents[2]

class DesignBuildQAError(RuntimeError): pass

def _load(path: Path) -> dict[str, Any]:
    if not path.exists(): raise DesignBuildQAError(f"Missing QA input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise DesignBuildQAError(f"Expected mapping: {path}")
    return value

def evaluate(client_id: str, platform: str, *, root: Path = ROOT) -> dict[str, Any]:
    p=root/"client-projects"/client_id
    approval=_load(p/"approved"/"experience-approval.yaml")
    ir=_load(p/"experience"/"design"/"design-ir.yaml")
    checks=[]
    for semantic_id in ir.get("components",[]):
        try:
            mapping=resolve_component(semantic_id,platform,root=root,client_id=client_id)
            checks.append({"id":f"mapping:{semantic_id}","passed":True,"evidence":str(mapping[platform])})
        except ResolverError as exc:
            checks.append({"id":f"mapping:{semantic_id}","passed":False,"evidence":str(exc)})
    evidence_path=p/"experience"/"qa"/f"{platform}-render-evidence.yaml"
    if evidence_path.exists():
        observed=_load(evidence_path)
        checks.append({"id":"render-evidence","passed":observed.get("status")=="passed","evidence":str(evidence_path.relative_to(root))})
    else:
        checks.append({"id":"render-evidence","passed":False,"evidence":f"missing {evidence_path.relative_to(root)}"})
    value={
        "client_id":client_id,
        "design_revision":approval.get("design_revision","unknown"),
        "platform":platform,
        "checks":checks,
        "status":"passed" if checks and all(x["passed"] for x in checks) else "blocked",
    }
    errors=validate_document(value,"design-build-evidence")
    if errors: raise DesignBuildQAError("; ".join(errors))
    return value

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--client",required=True);ap.add_argument("--platform",choices=["flutter","web"],required=True);ap.add_argument("--root",type=Path,default=ROOT)
    a=ap.parse_args()
    try:
        value=evaluate(a.client,a.platform,root=a.root);print(yaml.safe_dump(value,sort_keys=False));return 0 if value["status"]=="passed" else 2
    except DesignBuildQAError as exc:
        print(f"design-build-qa-error: {exc}");return 2

if __name__=="__main__": raise SystemExit(main())
