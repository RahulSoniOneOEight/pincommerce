from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "platform" / "capabilities" / "registry.yaml"


class CapabilityError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CapabilityError(f"Missing required artifact: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CapabilityError(f"Expected mapping in {path}")
    return value


def discover(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    try:
        validate_identifier(client_id, kind="client_id")
    except IdentifierError as exc:
        raise CapabilityError(str(exc)) from exc

    project = root / "client-projects" / client_id
    capability_map = load_yaml(project / "derived" / "capability-map.yaml")
    registry = load_yaml(root / "platform" / "capabilities" / "registry.yaml")

    required = set()
    for key in ("mandatory", "core", "recommended", "requested_additional"):
        required.update(capability_map.get(key, []) or [])

    discovered = []
    covered = set()
    for domain, entry in registry.get("capabilities", {}).items():
        offered = set(entry.get("capabilities", []))
        matched = sorted(required & offered)
        if not matched:
            continue
        adapter = entry.get("adapter")
        adapter_exists = True if not adapter else (root / adapter).exists()
        action = "RETAIN" if adapter_exists else "UPGRADE"
        discovered.append({
            "domain": domain,
            "runtime": entry.get("runtime"),
            "matched_capabilities": matched,
            "adapter": adapter,
            "adapter_exists": adapter_exists,
            "classification": action,
        })
        covered.update(matched)

    gaps = sorted(required - covered)
    return {
        "client_id": client_id,
        "registry_version": registry.get("version", 1),
        "required_capabilities": sorted(required),
        "discovered": discovered,
        "unmapped_capabilities": gaps,
        "policy": {
            "allowed_classifications": registry.get("policy", {}).get("reuse_actions", []),
            "build_new_only_after_discovery": True,
        },
        "status": "complete" if not gaps else "gaps-present",
    }


def write(client_id: str, root: Path = ROOT, overwrite: bool = False) -> Path:
    path = root / "client-projects" / client_id / "derived" / "capability-discovery.yaml"
    if path.exists() and not overwrite:
        raise CapabilityError(f"Refusing to overwrite: {path}")
    value = discover(client_id, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover reusable PinCommerce capabilities for a client")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--print-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        if args.print_only:
            print(yaml.safe_dump(discover(args.client, args.root), sort_keys=False).strip())
        else:
            print(write(args.client, args.root, args.overwrite).relative_to(args.root))
        return 0
    except CapabilityError as exc:
        print(f"capability-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
