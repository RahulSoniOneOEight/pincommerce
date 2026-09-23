from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from tooling.experience.visual_tournament import select_review_winner
from tooling.experience.learning_pipeline import rank_candidates
ROOT=Path(__file__).resolve().parents[2]

def load(path: Path)->Any: return yaml.safe_load(path.read_text(encoding="utf-8"))

def run(client: str, root: Path=ROOT)->dict[str,Any]:
    base=root/"client-projects"/client/"experience"/"design"
    tournament=load(base/"tournament.yaml")
    ledger=load(base/"learning-ledger.yaml")
    result=select_review_winner(tournament["candidates"],tournament["weights"],tournament.get("minimum_score",80))
    base_scores=[{"id":c["id"],"base_score":c["score"]} for c in result["candidates"]]
    ranking=rank_candidates(base_scores,ledger["outcomes"],ledger["telemetry"])
    return {
      "version":1,"client_id":client,"tournament_winner":result["winner"]["id"],
      "status":ranking["status"],"requires_human_approval":ranking["requires_human_approval"],
      "ranking":[{k:r[k] for k in ("id","base_score","learning_adjustment","advisory_score")} for r in ranking["candidates"]],
      "guardrails":{
        "auto_promote": bool(ranking["learning"]["guardrails"].get("auto_promote",False)),
        "mutate_approved_client_design": bool(ranking["learning"]["guardrails"].get("mutate_approved_client_design",False))
      }
    }

def assert_drift_free(client: str,root:Path=ROOT)->dict[str,Any]:
    expected=load(root/"client-projects"/client/"experience"/"design"/"learning-run.yaml")
    actual=run(client,root)
    return {"status":"passed" if actual==expected else "blocked","actual":actual,"expected":expected}

def main():
    import argparse,json
    p=argparse.ArgumentParser(); p.add_argument("--client",required=True); a=p.parse_args()
    r=assert_drift_free(a.client); print(json.dumps(r,indent=2)); return 0 if r["status"]=="passed" else 2
if __name__=="__main__": raise SystemExit(main())
