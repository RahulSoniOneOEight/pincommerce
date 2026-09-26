from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import hashlib
import yaml

ROOT = Path(__file__).resolve().parents[2]

class DesignGateError(RuntimeError):
    pass

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DesignGateError(f"Missing design-gate artifact: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DesignGateError(f"Expected mapping: {path}")
    return value

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def assert_build_allowed(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    p = root / "client-projects" / client_id
    approval_path = p / "approved" / "experience-approval.yaml"
    approval = _load(approval_path)
    if approval.get("decision") != "approved" or approval.get("immutable") is not True:
        raise DesignGateError("Experience approval is not immutable/approved")
    package_path = p / approval["review_package_ref"]
    package = _load(package_path)
    if package.get("design_revision") != approval.get("design_revision"):
        raise DesignGateError("Approved design revision does not match review package")
    if package.get("source_revision") != approval.get("source_revision"):
        raise DesignGateError("Approved source revision does not match review package")
    penpot_ref = package.get("penpot_ref")
    if not penpot_ref:
        raise DesignGateError("Approved review package has no Penpot revision")
    design_ir = _load(p / "experience" / "design" / "design-ir.yaml")
    component_registry = _load(p / "experience" / "design" / "component-contract-registry.yaml")
    if design_ir.get("status") not in {"review-ready","approved"}:
        raise DesignGateError("Design IR is not review-ready/approved")
    if component_registry.get("status") not in {"review-ready","approved"}:
        raise DesignGateError("Component contracts are not review-ready/approved")
    return {
        "client_id": client_id,
        "allowed": True,
        "approval_id": approval["approval_id"],
        "design_revision": approval["design_revision"],
        "penpot_ref": penpot_ref,
        "design_ir_sha256": _sha(p / "experience" / "design" / "design-ir.yaml"),
        "component_registry_sha256": _sha(p / "experience" / "design" / "component-contract-registry.yaml"),
    }

def main() -> int:
    ap=argparse.ArgumentParser(description="Hard gate for client-facing production UI build")
    ap.add_argument("--client",required=True); ap.add_argument("--root",type=Path,default=ROOT)
    args=ap.parse_args()
    try:
        print(yaml.safe_dump(assert_build_allowed(args.client,args.root),sort_keys=False))
        return 0
    except DesignGateError as exc:
        print(f"design-gate-error: {exc}")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
