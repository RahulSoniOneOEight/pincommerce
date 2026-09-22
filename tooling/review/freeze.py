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
from tooling.review.visual_qa import REQUIRED_CHECKS
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


def _assert_truth_ready(project: Path) -> None:
    truth = load_yaml(project / "derived" / "truth-register.yaml")
    errors = validate_document(truth, "truth-register")
    if errors:
        raise FreezeError("Invalid Client Truth Register: " + "; ".join(errors))
    if truth.get("status") not in {"review-ready", "approved"}:
        raise FreezeError("Client Truth Register must be review-ready/approved before scope freeze")
    if truth.get("open_questions"):
        raise FreezeError("Client Truth Register has unresolved open questions")
    if truth.get("conflicts"):
        raise FreezeError("Client Truth Register has unresolved conflicts")
    unresolved = [
        item.get("truth_id", "unknown")
        for item in truth.get("records", [])
        if item.get("classification") in {"assumption", "unknown", "conflict"}
        and item.get("status") not in {"confirmed", "resolved", "rejected"}
    ]
    if unresolved:
        raise FreezeError(
            "Client Truth Register has unresolved records: " + ", ".join(unresolved)
        )


def _accepted_architecture_decisions(project: Path) -> list[str]:
    refs: list[str] = []
    blocking: list[str] = []
    for path in sorted((project / "solution" / "decisions").glob("ADR-*.yaml")):
        decision = load_yaml(path)
        errors = validate_document(decision, "architecture-decision")
        if errors:
            raise FreezeError(f"Invalid architecture decision {path.name}: " + "; ".join(errors))
        if decision.get("status") != "accepted":
            blocking.append(path.name)
        else:
            refs.append(f"solution/decisions/{path.name}")
    if blocking:
        raise FreezeError(
            "All active Architecture Decisions must be accepted before scope freeze: "
            + ", ".join(blocking)
        )
    return refs


def _required_surfaces_and_journeys(project: Path) -> tuple[list[str], list[str]]:
    surface_map = load_yaml(project / "derived" / "surface-map.yaml")
    journey_map = load_yaml(project / "derived" / "journey-map.yaml")
    surfaces = list(dict.fromkeys(surface_map.get("required", [])))
    journeys = list(dict.fromkeys(
        item.get("id") if isinstance(item, dict) else item
        for item in journey_map.get("journeys", [])
        if not isinstance(item, dict) or item.get("status") == "required"
    ))
    return surfaces, [item for item in journeys if item]


def _assert_review_coverage(
    review: dict[str, Any],
    *,
    required_surfaces: list[str],
    required_journeys: list[str],
    direction_id: str,
) -> None:
    errors = validate_document(review, "review-session")
    if errors:
        raise FreezeError("Invalid Review Session: " + "; ".join(errors))
    if review.get("status") != "approved":
        raise FreezeError("Review Session must be approved before scope freeze")
    if review.get("direction_id") != direction_id:
        raise FreezeError("Review Session direction does not match selected direction")

    blocking_artifacts = [
        item.get("artifact_id", "unknown")
        for item in review.get("artifacts", [])
        if item.get("approval_status") != "approved"
    ]
    if blocking_artifacts:
        raise FreezeError(
            "All review artifacts must be approved: " + ", ".join(blocking_artifacts)
        )

    artifact_surfaces = {
        item.get("surface")
        for item in review.get("artifacts", [])
        if item.get("approval_status") == "approved"
    }
    missing_artifact_surfaces = [
        surface for surface in required_surfaces if surface not in artifact_surfaces
    ]
    if missing_artifact_surfaces:
        raise FreezeError(
            "Approved Review Session has no approved artifact for required surfaces: "
            + ", ".join(missing_artifact_surfaces)
        )

    surface_status = {
        item.get("surface"): item.get("status")
        for item in review.get("surface_approvals", [])
    }
    missing_surfaces = [
        surface for surface in required_surfaces
        if surface_status.get(surface) != "approved"
    ]
    if missing_surfaces:
        raise FreezeError(
            "Required surfaces are not approved: " + ", ".join(missing_surfaces)
        )

    journey_status = {
        item.get("journey"): item.get("status")
        for item in review.get("journey_approvals", [])
    }
    missing_journeys = [
        journey for journey in required_journeys
        if journey_status.get(journey) != "approved"
    ]
    if missing_journeys:
        raise FreezeError(
            "Required journeys are not approved: " + ", ".join(missing_journeys)
        )


def _validated_live_sessions(project: Path, review: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for raw_ref in review.get("live_review_sessions", []):
        relative = str(raw_ref)
        if relative.startswith("feedback/"):
            relative = relative[len("feedback/"):]
        path = project / "feedback" / relative
        live = load_yaml(path)
        errors = validate_document(live, "live-review-session")
        if errors:
            raise FreezeError(f"Invalid live review session {path.name}: " + "; ".join(errors))
        if live.get("review_id") != review.get("review_id"):
            raise FreezeError(
                f"Live review session {path.name} belongs to a different Review Session"
            )
        if live.get("status") not in {"client-confirmed", "closed"}:
            raise FreezeError(
                f"Live review session {path.name} must be client-confirmed/closed before scope freeze"
            )
        unrouted_material = [
            edit.get("edit_id", "unknown")
            for edit in live.get("edits", [])
            if edit.get("classification") == "material-change"
            and edit.get("status") != "change-contract-created"
        ]
        if unrouted_material:
            raise FreezeError(
                f"Live review session {path.name} has material edits without Change Contract: "
                + ", ".join(unrouted_material)
            )
        refs.append(f"feedback/{path.name}")
    return refs


def _assert_visual_qa(
    project: Path,
    visual_qa_files: list[str],
    *,
    review: dict[str, Any],
    required_surfaces: list[str],
) -> list[str]:
    qa_refs: list[str] = []
    qa_surfaces: set[str] = set()
    required_checks = set(REQUIRED_CHECKS)
    for name in visual_qa_files:
        qa = load_yaml(project / "experience" / "visual-qa" / name)
        errors = validate_document(qa, "visual-qa")
        if errors:
            raise FreezeError("Invalid visual QA: " + "; ".join(errors))
        if qa.get("build_identity") != review.get("build_id"):
            raise FreezeError(f"Visual QA {name} does not match Review Session build")
        if qa.get("direction_id") != review.get("direction_id"):
            raise FreezeError(f"Visual QA {name} does not match Review Session direction")
        if qa.get("status") != "passed":
            raise FreezeError(f"Visual QA {name} must be passed")
        checks = {item.get("id"): item.get("status") for item in qa.get("checks", [])}
        missing_checks = sorted(required_checks - set(checks))
        if missing_checks:
            raise FreezeError(
                f"Visual QA {name} is missing required checks: " + ", ".join(missing_checks)
            )
        failed = [check for check in REQUIRED_CHECKS if checks.get(check) != "pass"]
        if failed:
            raise FreezeError(
                f"Visual QA {name} has blocking checks: " + ", ".join(failed)
            )
        surface = qa.get("surface")
        if surface:
            qa_surfaces.add(surface)
        qa_refs.append(f"experience/visual-qa/{name}")

    missing_surfaces = [
        surface for surface in required_surfaces if surface not in qa_surfaces
    ]
    if missing_surfaces:
        raise FreezeError(
            "Passing Visual QA is missing for required surfaces: "
            + ", ".join(missing_surfaces)
        )
    return qa_refs



def _assert_revision_round(
    project: Path,
    review: dict[str, Any],
    *,
    expected_review_ref: str,
    required_surfaces: list[str],
    required_journeys: list[str],
    qa_refs: list[str],
) -> tuple[str, str]:
    revision_ref = review.get("prototype_revision_ref")
    round_ref = review.get("review_round_ref")
    if not revision_ref or not round_ref:
        raise FreezeError(
            "Review Session must be bound to a Prototype Revision and Review Round before scope freeze"
        )

    revision = load_yaml(project / revision_ref)
    round_value = load_yaml(project / round_ref)

    revision_errors = validate_document(revision, "prototype-revision")
    if revision_errors:
        raise FreezeError("Invalid Prototype Revision: " + "; ".join(revision_errors))
    round_errors = validate_document(round_value, "review-round")
    if round_errors:
        raise FreezeError("Invalid Review Round: " + "; ".join(round_errors))

    if revision.get("build_id") != review.get("build_id"):
        raise FreezeError("Prototype Revision build does not match Review Session")
    if round_value.get("prototype_revision_ref") != revision_ref:
        raise FreezeError("Review Round does not reference the selected Prototype Revision")
    if round_value.get("review_session_ref") != expected_review_ref:
        raise FreezeError("Review Round does not reference the selected Review Session")
    if round_value.get("outcome") != "approved":
        raise FreezeError("Final Review Round must be approved before scope freeze")
    round_qa = set(round_value.get("qa_refs", []))
    if not round_qa:
        raise FreezeError("Final Review Round has no QA evidence")
    if not round_qa.issubset(set(qa_refs)):
        raise FreezeError("Final Review Round QA references do not match selected passing QA")

    surface_status = {
        item.get("surface"): item.get("status")
        for item in round_value.get("surface_decisions", [])
    }
    missing_surfaces = [
        surface for surface in required_surfaces
        if surface_status.get(surface) != "approved"
    ]
    if missing_surfaces:
        raise FreezeError(
            "Final Review Round is missing approved surfaces: " + ", ".join(missing_surfaces)
        )

    journey_status = {
        item.get("journey"): item.get("status")
        for item in round_value.get("journey_decisions", [])
    }
    missing_journeys = [
        journey for journey in required_journeys
        if journey_status.get(journey) != "approved"
    ]
    if missing_journeys:
        raise FreezeError(
            "Final Review Round is missing approved journeys: " + ", ".join(missing_journeys)
        )

    unresolved_feedback = []
    for feedback_ref in round_value.get("feedback_refs", []):
        feedback = load_yaml(project / feedback_ref)
        errors = validate_document(feedback, "review-feedback")
        if errors:
            raise FreezeError(
                f"Invalid Review Feedback {feedback_ref}: " + "; ".join(errors)
            )
        if feedback.get("round_id") != round_value.get("round_id"):
            raise FreezeError(f"Review Feedback {feedback_ref} belongs to another round")
        if feedback.get("status") not in {"resolved", "accepted", "rejected"}:
            unresolved_feedback.append(feedback.get("feedback_id", feedback_ref))
    if unresolved_feedback:
        raise FreezeError(
            "Final Review Round has unresolved feedback: " + ", ".join(unresolved_feedback)
        )

    return revision_ref, round_ref

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
    _assert_truth_ready(project)

    solution = load_yaml(project / "solution" / "solution-contract.yaml")
    capability_map = load_yaml(project / "derived" / "capability-map.yaml")
    review = load_yaml(project / "feedback" / review_file)
    direction = load_yaml(project / "experience" / "directions" / direction_file)
    required_surfaces, required_journeys = _required_surfaces_and_journeys(project)

    try:
        coverage = assert_client_review_ready(client_id, direction_file, root)
    except CoverageError as exc:
        raise FreezeError("Prototype completeness changed since review: " + str(exc)) from exc

    core_runtime = None
    if client_requires_core_runtime(client_id, root):
        try:
            core_runtime = assert_core_runtime_ready(client_id, root)
        except CoreRuntimeError as exc:
            raise FreezeError("Functional core runtime is not ready: " + str(exc)) from exc

    _assert_review_coverage(
        review,
        required_surfaces=required_surfaces,
        required_journeys=required_journeys,
        direction_id=direction["direction_id"],
    )

    expected_coverage_ref = f"experience/prototypes/{direction_file.replace('.yaml', '')}-coverage.yaml"
    if review.get("coverage_ref") != expected_coverage_ref:
        raise FreezeError("Review Session coverage_ref does not match selected prototype")
    if review.get("implementation_ref") != coverage.get("implementation_ref"):
        raise FreezeError("Review Session implementation_ref is stale")
    if core_runtime is not None:
        if review.get("core_runtime_ref") != "experience/prototype-core-runtime.yaml":
            raise FreezeError("Review Session core_runtime_ref is missing/stale")
        if review.get("demo_dataset_ref") != core_runtime.get("demo_dataset_ref"):
            raise FreezeError("Review Session demo_dataset_ref is missing/stale")
    elif review.get("core_runtime_ref") is not None:
        raise FreezeError("Review Session references a core runtime that is not required")

    qa_refs = _assert_visual_qa(
        project,
        visual_qa_files,
        review=review,
        required_surfaces=required_surfaces,
    )
    revision_ref, round_ref = _assert_revision_round(
        project,
        review,
        expected_review_ref=f"feedback/{review_file}",
        required_surfaces=required_surfaces,
        required_journeys=required_journeys,
        qa_refs=qa_refs,
    )
    live_sessions = _validated_live_sessions(project, review)
    architecture_refs = _accepted_architecture_decisions(project)

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
        "truth_ref": "derived/truth-register.yaml",
        "solution_ref": "solution/solution-contract.yaml",
        "experience_ref": f"experience/directions/{direction_file}",
        "prototype_revision_ref": revision_ref,
        "review_round_ref": round_ref,
        "prototype_coverage_ref": expected_coverage_ref,
        "prototype_implementation_ref": coverage.get("implementation_ref"),
        "core_runtime_ref": (
            "experience/prototype-core-runtime.yaml" if core_runtime is not None else None
        ),
        "demo_dataset_ref": core_runtime.get("demo_dataset_ref") if core_runtime else None,
        "build_id": review["build_id"],
        "review_ref": f"feedback/{review_file}",
        "visual_qa_refs": qa_refs,
        "approved_surfaces": required_surfaces,
        "approved_journeys": required_journeys,
        "included_capabilities": included,
        "excluded_capabilities": list(capability_map.get("not_applicable", [])),
        "deferred_capabilities": list(capability_map.get("later", [])),
        "architecture_decisions": architecture_refs,
        "open_non_blocking_items": [],
        "live_review_sessions": live_sessions,
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
