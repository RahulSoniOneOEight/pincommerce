from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from tooling.experience.generator import build_experience
from tooling.onboarding.engine import build_blueprint

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _approval_normalized(relative: str, value: object) -> object:
    """Ignore human approval metadata while still checking generated ADR substance."""
    if relative.startswith("solution/decisions/ADR-") and isinstance(value, dict):
        result = dict(value)
        result["status"] = "proposed"
        result["approved_by"] = None
        result["approved_at"] = None
        return result
    return value


def blueprint_drift(client_id: str, root: Path = ROOT) -> list[str]:
    """Return drift between the onboarding generator and committed derived artifacts."""
    blueprint = build_blueprint(client_id, root)
    project = root / "client-projects" / client_id
    errors: list[str] = []
    for relative, generated in blueprint.files.items():
        path = project / relative
        if not path.exists():
            errors.append(f"missing generated artifact: {relative}")
            continue
        committed = _approval_normalized(relative, _load(path))
        expected = _approval_normalized(relative, generated)
        if committed != expected:
            errors.append(f"drift: {relative}")
    return errors


def experience_drift(client_id: str, root: Path = ROOT) -> list[str]:
    """Return drift between the experience generator and committed experience artifacts."""
    files = build_experience(client_id, root)
    project = root / "client-projects" / client_id
    errors: list[str] = []
    for relative, generated in files.items():
        path = project / relative
        if not path.exists():
            errors.append(f"missing generated artifact: {relative}")
            continue
        if _load(path) != generated:
            errors.append(f"drift: {relative}")
    return errors


def check(client_id: str, root: Path = ROOT) -> list[str]:
    return blueprint_drift(client_id, root) + experience_drift(client_id, root)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail if committed generated artifacts differ from the generators"
    )
    parser.add_argument("--client", default="reference-retail")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    errors = check(args.client, args.root)
    if errors:
        print("Generated-artifact drift detected:")
        for error in errors:
            print(f"- {error}")
        print("Regenerate with: python -m tooling.onboarding.engine --client "
              f"{args.client} --overwrite && python -m tooling.experience.generator "
              f"--client {args.client} --overwrite")
        return 1
    print(f"Generated artifacts for {args.client} match committed copies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
