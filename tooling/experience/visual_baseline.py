from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
ROOT=Path(__file__).resolve().parents[2]
BASELINE=ROOT/"design-intelligence"/"approved-visual-baselines.yaml"

def load_baselines(path: Path=BASELINE)->dict[str,Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def compare_hashes(evidence: dict[str,Any], baseline: dict[str,Any]|None=None)->dict[str,Any]:
    baseline=baseline or load_baselines()
    approved=baseline["captures"]; blockers=[]
    seen=set()
    for row in evidence.get("captures",[]):
        p=str(row["pattern"]); v=str(row["viewport_id"]); seen.add((p,v))
        expected=approved.get(p,{}).get(v)
        if expected is None: blockers.append(f"baseline-missing:{p}:{v}")
        elif row.get("screenshot_sha256") != expected: blockers.append(f"pixel-baseline-changed:{p}:{v}")
    for p,views in approved.items():
        for v in views:
            if (p,v) not in seen: blockers.append(f"capture-missing:{p}:{v}")
    return {"status":"passed" if not blockers else "blocked","blocking_items":blockers,"mode":baseline.get("mode")}
