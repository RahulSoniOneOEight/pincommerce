from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from tooling.review.change_loop import plan as build_plan
from tooling.experience.critics import design_critic, journey_critic
from tooling.experience.visual_critic import evaluate as visual_critic
from tooling.intelligence.journey_engine import build as build_journeys
from tooling.orchestrator.phase1_build import build_components, build_design_ir
from tooling.onboarding.abc_completion import build_integration_map

ROOT=Path(__file__).resolve().parents[2]

class RegenerationError(RuntimeError): pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise RegenerationError(f"Missing regeneration input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RegenerationError(f"Expected mapping: {path}")
    return value

def _write(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(value,sort_keys=False),encoding="utf-8")

def execute(client_id:str,feedback_refs:list[str],root:Path=ROOT,dry_run:bool=True)->dict[str,Any]:
    p=root/"client-projects"/client_id
    plan=build_plan(client_id,feedback_refs,root)
    actions=[]
    for rel in plan["regenerate"]:
        actions.append({"artifact":rel,"action":"invalidate-and-regenerate","executed":False})
    qa_results={}
    if not dry_run:
        invalidated=p/"changes"/"regeneration-plan.yaml"
        _write(invalidated,plan)
        for rel in plan["regenerate"]:
            if rel=="derived/journey-graph.yaml":
                _write(p/rel,build_journeys(client_id,root))
            elif rel=="experience/design/component-contract-registry.yaml":
                _write(p/rel,build_components(client_id,root))
            elif rel=="experience/design/design-ir.yaml":
                _write(p/rel,build_design_ir(client_id,root))
            elif rel=="derived/integration-map.yaml":
                client_input=_load(p/"input"/"client-input.yaml")
                _write(p/rel,build_integration_map(client_input))
        if "design" in plan["required_qa"]:
            qa_results["design"]=design_critic(client_id,root)
            _write(p/"experience"/"qa"/"design-critic-v2.yaml",qa_results["design"])
        if "journey" in plan["required_qa"]:
            qa_results["journey"]=journey_critic(client_id,root)
            _write(p/"experience"/"qa"/"journey-critic-v2.yaml",qa_results["journey"])
        if "visual" in plan["required_qa"]:
            qa_results["visual"]=visual_critic(client_id,root)
            _write(p/"experience"/"qa"/"visual-semantic-critic.yaml",qa_results["visual"])
        for x in actions: x["executed"]=True
    return {"client_id":client_id,"plan":plan,"actions":actions,"qa_results":qa_results,"status":"planned" if dry_run else "executed"}
