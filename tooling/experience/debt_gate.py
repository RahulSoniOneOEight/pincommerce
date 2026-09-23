from __future__ import annotations
from pathlib import Path
import yaml
from tooling.experience.design_debt import scan
ROOT=Path(__file__).resolve().parents[2]
BASELINE=ROOT/"design-intelligence"/"design-debt-baseline.yaml"

def _key(item):
    if item.get("path"): return (item.get("type"),item.get("path"))
    return (item.get("type"),tuple(item.get("families",[])))

def evaluate(root: Path=ROOT):
    baseline=yaml.safe_load(BASELINE.read_text(encoding="utf-8"))
    allowed={_key(x) for x in baseline.get("allowed_findings",[])}
    current=scan(root)
    new=[x for x in current["findings"] if _key(x) not in allowed]
    return {"status":"passed" if not new else "blocked","new_findings":new,"finding_count":current["finding_count"]}

def main():
    import json
    r=evaluate(); print(json.dumps(r,indent=2)); return 0 if r["status"]=="passed" else 2
if __name__=="__main__": raise SystemExit(main())
