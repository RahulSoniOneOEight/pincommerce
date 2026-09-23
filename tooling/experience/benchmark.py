from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT=Path(__file__).resolve().parents[2]


class BenchmarkError(RuntimeError):
    pass


def load_yaml(path: Path)->dict[str,Any]:
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise BenchmarkError(f"Expected mapping in {path}")
    return value


def build_benchmarks(client_id:str, root:Path=ROOT)->list[dict[str,Any]]:
    project=root/"client-projects"/client_id
    selection=load_yaml(project/"experience"/"design"/"selection.yaml")
    results=[]
    for pattern in selection.get("patterns",[]):
        candidates=list(pattern.get("candidates",[]))
        if len(candidates)<2:
            continue
        record={
            "benchmark_id":f"BENCH-{client_id}-{pattern['pattern']}",
            "client_id":client_id,
            "pattern":pattern["pattern"],
            "candidates":candidates,
            "viewports":["mobile-390","tablet-768","desktop-1440"],
            "states":["default","loading","empty","error"],
            "fixture_ref":"experience/fixtures/commerce-baseline.yaml",
            "capture_rules":[
                "same-data",
                "same-semantic-theme",
                "same-viewport",
                "same-state",
                "same-content",
            ],
            "evaluation":[
                "functional-fit",
                "accessibility",
                "performance",
                "visual-quality",
                "brand-fit",
            ],
            "status":"planned",
        }
        errors=validate_document(record,"component-benchmark")
        if errors:
            raise BenchmarkError("; ".join(errors))
        results.append(record)
    return results


def main()->int:
    parser=argparse.ArgumentParser(description="Plan equal-fixture component benchmark tournaments")
    parser.add_argument("--client",required=True)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    values=build_benchmarks(args.client,args.root)
    payload={"client_id":args.client,"benchmarks":values}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(yaml.safe_dump(payload,sort_keys=False),encoding="utf-8")
    print(yaml.safe_dump(payload,sort_keys=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
