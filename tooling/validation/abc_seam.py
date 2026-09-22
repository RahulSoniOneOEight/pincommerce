from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.experience.coverage import CoverageError, assert_client_review_ready
from tooling.prototype.core_runtime import (
    CoreRuntimeError,
    assert_core_runtime_ready,
    client_requires_core_runtime,
)

ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping in {path}")
    return value


def audit_client(client_id: str, root: Path = ROOT, direction_file: str = "a.yaml") -> dict[str, Any]:
    project = root / "client-projects" / client_id
    blockers: dict[str, list[str]] = {"A": [], "B": [], "C": []}

    # A — truth/intelligence
    try:
        truth = load_yaml(project / "derived" / "truth-register.yaml")
        errors = validate_document(truth, "truth-register")
        blockers["A"].extend(errors)
        if truth.get("status") not in {"review-ready", "approved"}:
            blockers["A"].append("truth-register is not review-ready/approved")
        if truth.get("open_questions"):
            blockers["A"].append("truth-register has open questions")
        if truth.get("conflicts"):
            blockers["A"].append("truth-register has unresolved conflicts")
        unresolved = [
            item.get("truth_id", "unknown")
            for item in truth.get("records", [])
            if item.get("classification") in {"assumption", "unknown", "conflict"}
            and item.get("status") not in {"confirmed", "resolved", "rejected"}
        ]
        if unresolved:
            blockers["A"].append("unresolved truth records: " + ", ".join(unresolved))
    except Exception as exc:
        blockers["A"].append(str(exc))

    for relative in (
        "derived/client-profile.yaml",
        "derived/industry-profile.yaml",
        "derived/benchmark-report.yaml",
        "derived/capability-gap.yaml",
    ):
        if not (project / relative).exists():
            blockers["A"].append(f"missing {relative}")

    # B — solution intelligence / architecture
    for relative in (
        "derived/reuse-decisions.yaml",
        "derived/capability-map.yaml",
        "derived/journey-map.yaml",
        "derived/entity-map.yaml",
        "derived/surface-map.yaml",
        "derived/integration-map.yaml",
        "derived/dependency-map.yaml",
        "solution/solution-contract.yaml",
    ):
        if not (project / relative).exists():
            blockers["B"].append(f"missing {relative}")

    for path in sorted((project / "solution" / "decisions").glob("ADR-*.yaml")):
        try:
            decision = load_yaml(path)
            errors = validate_document(decision, "architecture-decision")
            blockers["B"].extend(f"{path.name}: {error}" for error in errors)
            if decision.get("status") != "accepted":
                blockers["B"].append(f"{path.name} is {decision.get('status')}, not accepted")
        except Exception as exc:
            blockers["B"].append(f"{path.name}: {exc}")

    # C — functional prototype readiness
    try:
        assert_client_review_ready(client_id, direction_file, root)
    except CoverageError as exc:
        blockers["C"].append(str(exc))
    except Exception as exc:
        blockers["C"].append(str(exc))

    if client_requires_core_runtime(client_id, root):
        try:
            assert_core_runtime_ready(client_id, root)
        except CoreRuntimeError as exc:
            blockers["C"].append(str(exc))
        except Exception as exc:
            blockers["C"].append(str(exc))

    return {
        "client_id": client_id,
        "direction": direction_file,
        "phases": {
            phase: {
                "status": "ready" if not items else "blocked",
                "blockers": items,
            }
            for phase, items in blockers.items()
        },
        "ready_for_client_review": not any(blockers.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit A/B/C readiness end-to-end")
    parser.add_argument("--client", required=True)
    parser.add_argument("--direction", default="a.yaml")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = audit_client(args.client, args.root, args.direction)
    print(yaml.safe_dump(result, sort_keys=False))
    return 0 if result["ready_for_client_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
