from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]


class FreezeError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FreezeError(f"Missing approval input: {path}")
    with path.open("r", encoding="utf-8") as fh:
        value = yaml.safe_load(fh)
    if not isinstance(value, dict):
        raise FreezeError(f"Expected mapping in {path}")
    return value


def build_scope_baseline(
    client_id: str,
    *,
    review_file: str,
    visual_qa_files: list[str],
    approved_by: str,
    approved_at: str,
    direction_file: str = "a.yaml",
    version: int = 1,
    root: Path = ROOT,
) -> dict[str, Any]:
    try:
        validate_identifier(client_id, kind="client_id")
        validate_identifier(review_file, kind="review filename")
        validate_identifier(direction_file, kind="direction filename")
        for name in visual_qa_files:
            validate_identifier(name, kind="visual qa filename")
    except IdentifierError as exc:
        raise FreezeError(str(exc)) from exc

    project = root / "client-projects" / client_id
    solution = load_yaml(project / "solution" / "solution-contract.yaml")
    capability_map = load_yaml(project / "derived" / "capability-map.yaml")
    review = load_yaml(project / "feedback" / review_file)
    direction = load_yaml(project / "experience" / "directions" / direction_file)

    if review.get("status") != "approved":
        raise FreezeError("Review Session must be approved before scope freeze")
    blocking = [
        item["artifact_id"] for item in review.get("artifacts", [])
        if item.get("approval_status") != "approved"
    ]
    if blocking:
        raise FreezeError("All review artifacts must be approved: " + ", ".join(blocking))

    qa_refs: list[str] = []
    for name in visual_qa_files:
        qa = load_yaml(project / "experience" / "visual-qa" / name)
        errors = validate_document(qa, "visual-qa")
        if errors:
            raise FreezeError("Invalid visual QA: " + "; ".join(errors))
        if qa.get("status") not in {"passed", "review-ready"}:
            raise FreezeError(f"Visual QA {name} is not passed/review-ready")
        failed = [c.get("id", "unknown") for c in qa.get("checks", []) if c.get("status") != "pass"]
        if failed:
            raise FreezeError(f"Visual QA {name} has blocking checks: {', '.join(failed)}")
        qa_refs.append(f"experience/visual-qa/{name}")

    included = list(dict.fromkeys(
        capability_map.get("mandatory", [])
        + capability_map.get("core", [])
        + capability_map.get("recommended", [])
        + capability_map.get("requested_additional", [])
    ))

    baseline = {
        "baseline_id": f"BASE-{client_id}-v{version}",
        "client_id": client_id,
        "version": version,
        "solution_ref": "solution/solution-contract.yaml",
        "experience_ref": f"experience/directions/{direction_file}",
        "review_ref": f"feedback/{review_file}",
        "visual_qa_refs": qa_refs,
        "included_capabilities": included,
        "excluded_capabilities": list(capability_map.get("not_applicable", [])),
        "deferred_capabilities": list(capability_map.get("later", [])),
        "architecture_decisions": [
            f"solution/decisions/{path.name}"
            for path in sorted((project / "solution" / "decisions").glob("ADR-*.yaml"))
        ],
        "open_non_blocking_items": [],
        "approved_by": approved_by,
        "approved_at": approved_at,
        "immutable": True,
    }
    errors = validate_document(baseline, "scope-baseline")
    if errors:
        raise FreezeError("Generated baseline invalid: " + "; ".join(errors))
    return baseline


def write_scope_baseline(client_id: str, baseline: dict[str, Any], root: Path = ROOT) -> Path:
    path = root / "client-projects" / client_id / "approved" / "scope-baseline.yaml"
    if path.exists():
        raise FreezeError(f"Refusing to overwrite immutable baseline: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(baseline, fh, sort_keys=False)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze an approved A/B/C client baseline")
    parser.add_argument("--client", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--visual-qa", action="append", required=True)
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--approved-at", required=True)
    parser.add_argument("--direction", default="a.yaml")
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args()
    try:
        baseline = build_scope_baseline(
            args.client,
            review_file=args.review,
            visual_qa_files=args.visual_qa,
            approved_by=args.approved_by,
            approved_at=args.approved_at,
            direction_file=args.direction,
            version=args.version,
        )
        path = write_scope_baseline(args.client, baseline)
        print(path.relative_to(ROOT))
        return 0
    except FreezeError as exc:
        print(f"freeze-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
