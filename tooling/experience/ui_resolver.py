from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[2]

class ResolverError(RuntimeError): pass

def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ResolverError(f"Expected mapping: {path}")
    return value

def _registry(root: Path, client_id: str | None = None) -> dict[str, Any]:
    if client_id:
        candidate = root / "client-projects" / client_id / "experience" / "design" / "ui-implementation-registry.yaml"
        if candidate.exists():
            return _load(candidate)
    return _load(root / "platform" / "ui" / "implementation-registry.yaml")

def resolve_component(semantic_id: str, platform: str, *, root: Path = ROOT, client_id: str | None = None) -> dict[str, Any]:
    if platform not in {"flutter", "web"}:
        raise ResolverError("platform must be flutter or web")
    registry = _registry(root, client_id)
    item = next((x for x in registry.get("components", []) if x.get("semantic_id") == semantic_id or semantic_id in x.get("aliases", [])), None)
    if not item:
        raise ResolverError(f"No approved mapping for {semantic_id}")
    return {"semantic_id": semantic_id, "penpot": item["penpot"], platform: item[platform], "qa": item["qa"]}

def resolve_specialist(kind: str, platform: str, *, root: Path = ROOT, client_id: str | None = None) -> Any:
    registry = _registry(root, client_id)
    value = registry.get("specialists", {}).get(kind)
    if value is None:
        raise ResolverError(f"No specialist mapping for {kind}")
    if isinstance(value, dict) and platform in value:
        return value[platform]
    return value

def resolve_icon(semantic_id: str, platform: str, *, root: Path = ROOT, client_id: str | None = None) -> dict[str, Any]:
    path = root / "platform" / "ui" / "icon-registry.yaml"
    if client_id:
        candidate = root / "client-projects" / client_id / "experience" / "design" / "icon-registry.yaml"
        if candidate.exists(): path = candidate
    registry = _load(path)
    item = next((x for x in registry.get("icons", []) if x.get("semantic_id") == semantic_id), None)
    if not item:
        raise ResolverError(f"No approved icon mapping for {semantic_id}")
    if platform not in {"flutter","web","penpot"}:
        raise ResolverError("icon platform must be flutter, web, or penpot")
    return {"semantic_id": semantic_id, "family": item["family"], "name": item["name"], platform: item[platform]}

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("kind", choices=["component","specialist","icon"])
    ap.add_argument("name")
    ap.add_argument("--platform", required=True)
    ap.add_argument("--client")
    args=ap.parse_args()
    try:
        if args.kind=="component": value=resolve_component(args.name,args.platform,client_id=args.client)
        elif args.kind=="icon": value=resolve_icon(args.name,args.platform,client_id=args.client)
        else: value={"kind":args.name,"platform":args.platform,"mapping":resolve_specialist(args.name,args.platform,client_id=args.client)}
        print(yaml.safe_dump(value,sort_keys=False)); return 0
    except ResolverError as exc:
        print(f"ui-resolver-error: {exc}"); return 2

if __name__=="__main__": raise SystemExit(main())
