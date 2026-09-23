from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_CHECKS = (
    "design-contract",
    "responsive",
    "accessibility",
    "critical-states",
    "business-rules",
    "journey-coverage",
    "design-selection",
    "semantic-theme",
    "motion-and-reduced-motion",
    "asset-quality-and-source",
    "component-quality-threshold",
    "state-completeness",
    "performance-budget",
    "cross-platform-parity",
    "design-debt",
)


class VisualQaError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise VisualQaError(f"Missing visual QA input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VisualQaError(f"Expected mapping in {path}")
    return value


def plan_visual_qa(client_id: str, capture_file: str, root: Path = ROOT) -> dict[str, dict[str, Any]]:
    try:
        validate_identifier(client_id, kind="client_id")
        validate_identifier(capture_file, kind="capture filename")
    except IdentifierError as exc:
        raise VisualQaError(str(exc)) from exc

    project = root / "client-projects" / client_id
    capture = load_yaml(project / "experience" / "visual-qa" / capture_file)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in capture.get("targets", []):
        grouped[target["surface"]].append(target)

    if not grouped:
        raise VisualQaError("Capture manifest has no targets")

    files: dict[str, dict[str, Any]] = {}
    for surface, targets in sorted(grouped.items()):
        qa_id = f"VQA-{capture['build_id']}-{surface}"
        evidence = ", ".join(target["output"] for target in targets)
        record = {
            "qa_id": qa_id,
            "client_id": client_id,
            "direction_id": capture["direction_id"],
            "surface": surface,
            "build_identity": capture["build_id"],
            "checks": [
                {"id": check, "status": "not-run", "evidence": evidence, "notes": []}
                for check in REQUIRED_CHECKS
            ],
            "status": "draft",
        }
        errors = validate_document(record, "visual-qa")
        if errors:
            raise VisualQaError("Generated visual QA record invalid: " + "; ".join(errors))
        files[f"{qa_id}.yaml"] = record
    return files


def evaluate_visual_qa(record: dict[str, Any]) -> dict[str, Any]:
    result = dict(record)
    checks = list(result.get("checks", []))
    statuses = [item.get("status") for item in checks]
    if any(status == "fail" for status in statuses):
        result["status"] = "failed"
    elif checks and all(status == "pass" for status in statuses):
        result["status"] = "passed"
    elif any(status in {"warning", "pass"} for status in statuses):
        result["status"] = "review-ready"
    else:
        result["status"] = "draft"
    return result


def write_plan(client_id: str, capture_file: str, root: Path = ROOT) -> list[Path]:
    project = root / "client-projects" / client_id / "experience" / "visual-qa"
    planned = plan_visual_qa(client_id, capture_file, root)
    written = []
    for name, record in planned.items():
        path = project / name
        if path.exists():
            raise VisualQaError(f"Refusing to overwrite Visual QA record: {path}")
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan governed Visual + Business QA from a capture manifest")
    parser.add_argument("--client", required=True)
    parser.add_argument("--capture", required=True)
    args = parser.parse_args()
    try:
        for path in write_plan(args.client, args.capture):
            print(path.relative_to(ROOT))
        return 0
    except VisualQaError as exc:
        print(f"visual-qa-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
