from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]
PHASE1 = ROOT / "workflows" / "phase1-intelligent-build.yaml"


class OrchestratorError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise OrchestratorError(f"Missing required artifact: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OrchestratorError(f"Expected mapping in {path}")
    return value


def _project(client: str) -> Path:
    try:
        validate_identifier(client, kind="client_id")
    except IdentifierError as exc:
        raise OrchestratorError(str(exc)) from exc
    return ROOT / "client-projects" / client


def bootstrap_paths(client: str) -> dict[str, Path]:
    project = _project(client)
    return {
        "workflow_state": project / "workflow" / "workflow-state.yaml",
        "current_summary": project / "context" / "CURRENT.md",
        "handoff": project / "context" / "handoff.yaml",
        "decisions": project / "context" / "decisions.yaml",
    }


def status(client: str) -> dict[str, Any]:
    paths = bootstrap_paths(client)
    state = _load(paths["workflow_state"])
    phase = _load(PHASE1)
    stage_ids = [s["id"] for s in phase["stages"]]
    current = state.get("current_stage")
    return {
        "client_id": client,
        "canonical_workflow_stage": current,
        "phase1_stage_known": current in stage_ids,
        "blocked": bool(state.get("blocked", False)),
        "completed": list(state.get("completed", [])),
        "context": {name: path.exists() for name, path in paths.items()},
        "next_action": "resolve-blocker" if state.get("blocked") else "plan-current-stage",
    }


def execution_packet(client: str) -> dict[str, Any]:
    project = _project(client)
    state = _load(project / "workflow" / "workflow-state.yaml")
    phase = _load(PHASE1)
    current = state.get("current_stage")
    stage = next((s for s in phase["stages"] if s["id"] == current), None)
    if stage is None:
        raise OrchestratorError(
            f"Current canonical stage {current!r} is not a Phase-1 execution stage; "
            "use the existing lifecycle until an explicit stage mapping is defined."
        )
    return {
        "client": client,
        "current_stage": current,
        "objective": phase["objective"],
        "stage_contract": stage,
        "mandatory_rules": [
            "repository contracts are source of truth",
            "discover/reuse existing capability before building new",
            "references must be explicitly resolved",
            "do not modify approved upstream truth to make downstream validation pass",
            "stage completion requires validator/evidence, not agent assertion",
            "human gates require explicit approval",
        ],
        "do_not": [
            "silently ignore declared references",
            "self-approve builder output",
            "advance workflow without required evidence",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PinCommerce Phase-1 orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "packet"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--client", required=True)
    args = parser.parse_args()
    try:
        result = status(args.client) if args.command == "status" else execution_packet(args.client)
        print(yaml.safe_dump(result, sort_keys=False).strip())
        return 0
    except OrchestratorError as exc:
        print(f"orchestrator-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
