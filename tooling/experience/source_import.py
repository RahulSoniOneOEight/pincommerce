from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

SUPPORTED = {"figma","penpot","git","reference-site","brand-guide"}


class SourceImportError(RuntimeError):
    pass


def normalize(source_type: str, source_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if source_type not in SUPPORTED:
        raise SourceImportError(f"Unsupported source type: {source_type}")
    return {
        "source_id":source_id,
        "type":source_type,
        "components":payload.get("components", []),
        "tokens":payload.get("tokens", {}),
        "typography":payload.get("typography", {}),
        "spacing":payload.get("spacing", {}),
        "radii":payload.get("radii", {}),
        "colors":payload.get("colors", {}),
        "patterns":payload.get("patterns", []),
        "assets":payload.get("assets", []),
        "notes":payload.get("notes", []),
        "status":"normalized",
    }


def read_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower()==".json":
        value=json.loads(path.read_text(encoding="utf-8"))
    else:
        value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise SourceImportError("source export must be an object/mapping")
    return value


def main() -> int:
    parser=argparse.ArgumentParser(description="Normalize exported Figma/Penpot/Git/reference design metadata")
    parser.add_argument("--type",required=True,choices=sorted(SUPPORTED))
    parser.add_argument("--id",required=True)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    try:
        result=normalize(args.type,args.id,read_payload(args.input))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(yaml.safe_dump(result,sort_keys=False),encoding="utf-8")
        print(args.output)
        return 0
    except SourceImportError as exc:
        print(f"source-import-error: {exc}")
        return 2


if __name__=="__main__":
    raise SystemExit(main())
