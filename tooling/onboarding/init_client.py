from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate
from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]


class ClientInitError(RuntimeError):
    pass


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(value, fh, sort_keys=False)


def initialize_client(
    client_id: str,
    industry: str,
    business_models: list[str],
    goals: list[str] | None = None,
    requested_capabilities: list[str] | None = None,
    required_integrations: list[str] | None = None,
    geographies: list[str] | None = None,
    risk_profile: str = "standard",
    root: Path = ROOT,
) -> Path:
    try:
        validate_identifier(client_id, kind="client_id")
    except IdentifierError as exc:
        raise ClientInitError(str(exc)) from exc

    project = root / "client-projects" / client_id
    if project.exists():
        raise ClientInitError(f"Client project already exists: {project}")

    client_input = {
        "client_id": client_id,
        "industry": industry,
        "business_models": list(dict.fromkeys(business_models)),
        "goals": goals or [],
        "requested_capabilities": requested_capabilities or [],
        "required_integrations": required_integrations or [],
        "existing_systems": [],
        "constraints": [],
        "geographies": geographies or [],
        "risk_profile": risk_profile,
    }

    input_path = project / "input" / "client-input.yaml"
    write_yaml(input_path, client_input)

    if root == ROOT:
        errors = validate(input_path, "client-input")
        if errors:
            raise ClientInitError("Invalid client input: " + "; ".join(errors))

    workflow_state = {
        "client_id": client_id,
        "workflow_version": 1,
        "current_stage": "client-intake",
        "completed": [],
        "blocked": False,
        "human_approvals": [],
    }
    write_yaml(project / "workflow" / "workflow-state.yaml", workflow_state)

    for folder in (
        "input/documents",
        "intelligence/ai/decisions",
        "derived",
        "solution/decisions",
        "solution/architecture",
        "experience/directions",
        "experience/prototypes",
        "experience/builds",
        "experience/fixtures",
        "experience/captures",
        "experience/visual-qa",
        "feedback/reviews",
        "feedback/findings",
        "feedback/annotations",
        "changes",
        "approved",
        "contracts/contract-versions",
        "production",
        "qa",
        "uat",
        "release/candidates",
        "release/staging",
        "release/hardening",
        "release/observability",
        "release/releases",
        "release/recovery",
        "workflow/evidence",
    ):
        directory = project / folder
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch()

    return project


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a governed client project")
    parser.add_argument("--client", required=True)
    parser.add_argument("--industry", required=True)
    parser.add_argument("--business-model", action="append", required=True)
    parser.add_argument("--goal", action="append", default=[])
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--integration", action="append", default=[])
    parser.add_argument("--geography", action="append", default=[])
    parser.add_argument("--risk-profile", default="standard")
    args = parser.parse_args()

    try:
        project = initialize_client(
            client_id=args.client,
            industry=args.industry,
            business_models=args.business_model,
            goals=args.goal,
            requested_capabilities=args.capability,
            required_integrations=args.integration,
            geographies=args.geography,
            risk_profile=args.risk_profile,
        )
        print(f"Initialized client project: {project.relative_to(ROOT)}")
        print(
            "Next: complete intake, optionally add AI proposals through OpenCode, then run "
            f"'python -m tooling.onboarding.engine --client {args.client}'."
        )
        return 0
    except ClientInitError as exc:
        print(f"client-init-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
