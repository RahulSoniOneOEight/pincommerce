from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.experience.coverage import build_coverage

ROOT = Path(__file__).resolve().parents[2]


class PrototypeImplementationError(RuntimeError):
    pass


def build_implementation_plan(
    client_id: str,
    direction_file: str = "a.yaml",
    root: Path = ROOT,
) -> dict[str, Any]:
    coverage = build_coverage(
        client_id,
        direction_file,
        root,
        require_implementation=False,
    )
    suffix = direction_file.replace(".yaml", "")
    project = root / "client-projects" / client_id
    manifest_path = project / "experience" / "prototypes" / f"{suffix}-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    runtime_by_surface = {
        item["id"]: item.get("entry", f"external/{item['id']}")
        for item in manifest.get("surfaces", [])
    }

    surfaces = []
    for surface in coverage["surface_coverage"]:
        surfaces.append({
            "surface": surface["surface"],
            "runtime_ref": runtime_by_surface.get(surface["surface"], f"external/{surface['surface']}"),
            "screens": [
                {"id": item, "status": "pending", "evidence_ref": None}
                for item in surface["screens"]
            ],
            "components": [
                {"id": item, "status": "pending", "evidence_ref": None}
                for item in surface["components"]
            ],
            "states": [
                {"id": item, "status": "pending", "evidence_ref": None}
                for item in surface["states"]
            ],
            "status": "pending",
        })

    result = {
        "implementation_id": f"IMP-{client_id}-{suffix}",
        "client_id": client_id,
        "direction_id": coverage["direction_id"],
        "surfaces": surfaces,
        "status": "draft",
    }
    errors = validate_document(result, "prototype-implementation")
    if errors:
        raise PrototypeImplementationError(
            "Generated implementation plan invalid: " + "; ".join(errors)
        )
    return result


def write_implementation_plan(
    client_id: str,
    direction_file: str = "a.yaml",
    root: Path = ROOT,
    overwrite: bool = False,
) -> Path:
    value = build_implementation_plan(client_id, direction_file, root)
    suffix = direction_file.replace(".yaml", "")
    path = root / "client-projects" / client_id / "experience" / "prototypes" / f"{suffix}-implementation.yaml"
    if path.exists() and not overwrite:
        raise PrototypeImplementationError(f"Refusing to overwrite implementation evidence: {path}")
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create prototype screen/component/state implementation evidence plan"
    )
    parser.add_argument("--client", required=True)
    parser.add_argument("--direction", default="a.yaml")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        path = write_implementation_plan(
            args.client, args.direction, args.root, args.overwrite
        )
        print(path.relative_to(args.root))
        return 0
    except PrototypeImplementationError as exc:
        print(f"prototype-implementation-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
