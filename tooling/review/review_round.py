from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]

MATERIAL_TYPES = {
    "business-rule", "integration", "data", "finance", "security", "workflow"
}
MINOR_TYPES = {"visual", "content"}


class ReviewRoundError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ReviewRoundError(f"Missing review-round input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReviewRoundError(f"Expected mapping in {path}")
    return value


def save_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _direction_suffix(direction_id: str) -> str:
    return direction_id.split("-")[-1].lower()


def create_prototype_revision(
    client_id: str,
    *,
    review_file: str,
    sequence: int,
    created_by: str,
    parent_revision_ref: str | None = None,
    created_at: str | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    try:
        validate_identifier(client_id, kind="client_id")
        validate_identifier(review_file, kind="review filename")
    except IdentifierError as exc:
        raise ReviewRoundError(str(exc)) from exc
    if sequence < 1:
        raise ReviewRoundError("Prototype revision sequence must be >= 1")

    project = root / "client-projects" / client_id
    review = load_yaml(project / "feedback" / review_file)
    build = load_yaml(project / "experience" / "builds" / f"{review['build_id']}.yaml")

    if review.get("client_id") != client_id or build.get("client_id") != client_id:
        raise ReviewRoundError("Review/build client does not match target client")
    if review.get("direction_id") != build.get("direction_id"):
        raise ReviewRoundError("Review/build direction mismatch")

    suffix = _direction_suffix(review["direction_id"])
    revision_id = f"PROTO-{client_id}-{suffix}-{sequence:03d}"
    if parent_revision_ref:
        parent = load_yaml(project / parent_revision_ref)
        if parent.get("client_id") != client_id:
            raise ReviewRoundError("Parent Prototype Revision belongs to another client")
        if parent.get("direction_id") != review.get("direction_id"):
            raise ReviewRoundError("Parent Prototype Revision uses another direction")
        if int(parent.get("sequence", 0)) >= sequence:
            raise ReviewRoundError("Prototype Revision sequence must advance beyond parent")
    coverage = load_yaml(project / "experience" / "prototypes" / f"{suffix}-coverage.yaml")

    surfaces = [
        item["surface"] for item in coverage.get("surface_coverage", [])
        if item.get("required")
    ]
    journeys = list(dict.fromkeys(
        journey
        for item in coverage.get("surface_coverage", [])
        for journey in item.get("journeys", [])
    ))

    value = {
        "revision_id": revision_id,
        "client_id": client_id,
        "direction_id": review["direction_id"],
        "sequence": sequence,
        "parent_revision_ref": parent_revision_ref,
        "source_revision": build["source_revision"],
        "build_id": build["build_id"],
        "coverage_ref": review["coverage_ref"],
        "implementation_ref": review.get("implementation_ref"),
        "core_runtime_ref": review.get("core_runtime_ref"),
        "demo_dataset_ref": review.get("demo_dataset_ref"),
        "surfaces": surfaces,
        "journeys": journeys,
        "feedback_refs": [],
        "change_refs": [],
        "created_by": created_by,
        "created_at": created_at,
        "status": "review-ready",
        "immutable": True,
    }
    errors = validate_document(value, "prototype-revision")
    if errors:
        raise ReviewRoundError("Prototype Revision invalid: " + "; ".join(errors))
    return value


def create_review_round(
    client_id: str,
    *,
    revision_file: str,
    review_file: str,
    sequence: int,
    previous_round_ref: str | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    if sequence < 1:
        raise ReviewRoundError("Review round sequence must be >= 1")
    project = root / "client-projects" / client_id
    revision = load_yaml(project / "experience" / "revisions" / revision_file)
    review = load_yaml(project / "feedback" / review_file)

    if revision.get("client_id") != client_id or review.get("client_id") != client_id:
        raise ReviewRoundError("Revision/review client does not match target client")
    if revision.get("build_id") != review.get("build_id"):
        raise ReviewRoundError("Review Round must reference Review Session for the same build")

    suffix = _direction_suffix(revision["direction_id"])
    round_id = f"ROUND-{client_id}-{suffix}-{sequence:03d}"
    value = {
        "round_id": round_id,
        "client_id": client_id,
        "sequence": sequence,
        "prototype_revision_ref": f"experience/revisions/{revision_file}",
        "review_session_ref": f"feedback/{review_file}",
        "previous_round_ref": previous_round_ref,
        "next_revision_ref": None,
        "required_surfaces": list(revision["surfaces"]),
        "required_journeys": list(revision["journeys"]),
        "feedback_refs": [],
        "live_review_refs": list(review.get("live_review_sessions", [])),
        "change_refs": [],
        "qa_refs": [],
        "surface_decisions": [
            {"surface": item, "status": "pending"} for item in revision["surfaces"]
        ],
        "journey_decisions": [
            {"journey": item, "status": "pending"} for item in revision["journeys"]
        ],
        "outcome": "planned",
    }
    errors = validate_document(value, "review-round")
    if errors:
        raise ReviewRoundError("Review Round invalid: " + "; ".join(errors))
    return value


def classify_feedback(feedback_type: str, action: str) -> tuple[str, str]:
    if action == "approve":
        return "approval", "none"
    if action == "discuss":
        return "discussion", "discuss"
    if feedback_type in MINOR_TYPES:
        return "minor-change", "nowa"
    if feedback_type in MATERIAL_TYPES:
        return "material-change", "change-contract"
    return "discussion", "discuss"


def add_feedback(
    round_value: dict[str, Any],
    *,
    surface: str,
    comment: str,
    feedback_type: str,
    action: str,
    journey: str | None = None,
    screen: str | None = None,
    component: str | None = None,
    evidence_ref: str | None = None,
    created_by: str | None = None,
    created_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if surface not in round_value.get("required_surfaces", []):
        raise ReviewRoundError(f"Surface is not part of this Review Round: {surface}")
    if journey and journey not in round_value.get("required_journeys", []):
        raise ReviewRoundError(f"Journey is not part of this Review Round: {journey}")
    classification, route = classify_feedback(feedback_type, action)
    index = len(round_value.get("feedback_refs", [])) + 1
    feedback_id = f"FB-{round_value['round_id'][len('ROUND-'):]}-{index:03d}"
    feedback = {
        "feedback_id": feedback_id,
        "client_id": round_value["client_id"],
        "round_id": round_value["round_id"],
        "prototype_revision_ref": round_value["prototype_revision_ref"],
        "surface": surface,
        "journey": journey,
        "screen": screen,
        "component": component,
        "feedback_type": feedback_type,
        "comment": comment,
        "classification": classification,
        "route": route,
        "action": action,
        "status": "accepted" if action == "approve" else "open",
        "evidence_ref": evidence_ref,
        "live_review_ref": None,
        "change_contract_ref": None,
        "created_by": created_by,
        "created_at": created_at,
    }
    errors = validate_document(feedback, "review-feedback")
    if errors:
        raise ReviewRoundError("Review Feedback invalid: " + "; ".join(errors))

    updated = dict(round_value)
    updated["feedback_refs"] = list(updated.get("feedback_refs", [])) + [
        f"feedback/items/{feedback_id}.yaml"
    ]
    updated["outcome"] = "in-review"
    if action == "request-change":
        updated["outcome"] = "changes-requested"
        updated["surface_decisions"] = [
            {**item, "status": "changes-requested"}
            if item["surface"] == surface else item
            for item in updated["surface_decisions"]
        ]
        if journey:
            updated["journey_decisions"] = [
                {**item, "status": "changes-requested"}
                if item["journey"] == journey else item
                for item in updated["journey_decisions"]
            ]
    elif action == "approve":
        updated["surface_decisions"] = [
            {**item, "status": "approved"}
            if item["surface"] == surface else item
            for item in updated["surface_decisions"]
        ]
        if journey:
            updated["journey_decisions"] = [
                {**item, "status": "approved"}
                if item["journey"] == journey else item
                for item in updated["journey_decisions"]
            ]

    errors = validate_document(updated, "review-round")
    if errors:
        raise ReviewRoundError("Updated Review Round invalid: " + "; ".join(errors))
    return updated, feedback


def route_feedback(
    round_value: dict[str, Any],
    feedback: dict[str, Any],
    *,
    live_review_ref: str | None = None,
    change_contract_ref: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_feedback = dict(feedback)
    updated_round = dict(round_value)
    if feedback["route"] == "nowa":
        if not live_review_ref:
            raise ReviewRoundError("Minor feedback requires live_review_ref")
        updated_feedback["live_review_ref"] = live_review_ref
        updated_round["live_review_refs"] = list(dict.fromkeys(
            list(updated_round.get("live_review_refs", [])) + [live_review_ref]
        ))
    elif feedback["route"] == "change-contract":
        if not change_contract_ref:
            raise ReviewRoundError("Material feedback requires change_contract_ref")
        updated_feedback["change_contract_ref"] = change_contract_ref
        updated_round["change_refs"] = list(dict.fromkeys(
            list(updated_round.get("change_refs", [])) + [change_contract_ref]
        ))
    updated_feedback["status"] = "routed"
    for contract, value in (
        ("review-feedback", updated_feedback),
        ("review-round", updated_round),
    ):
        errors = validate_document(value, contract)
        if errors:
            raise ReviewRoundError(f"{contract} invalid: " + "; ".join(errors))
    return updated_round, updated_feedback


def resolve_feedback(feedback: dict[str, Any]) -> dict[str, Any]:
    result = {**feedback, "status": "resolved"}
    errors = validate_document(result, "review-feedback")
    if errors:
        raise ReviewRoundError("Resolved Review Feedback invalid: " + "; ".join(errors))
    return result


def record_qa(round_value: dict[str, Any], qa_refs: list[str]) -> dict[str, Any]:
    if not qa_refs:
        raise ReviewRoundError("At least one QA reference is required")
    result = {
        **round_value,
        "qa_refs": list(dict.fromkeys(list(round_value.get("qa_refs", [])) + qa_refs)),
    }
    errors = validate_document(result, "review-round")
    if errors:
        raise ReviewRoundError("Review Round invalid after QA: " + "; ".join(errors))
    return result


def approve_target(
    round_value: dict[str, Any],
    *,
    surface: str | None = None,
    journey: str | None = None,
) -> dict[str, Any]:
    if not surface and not journey:
        raise ReviewRoundError("surface or journey is required")
    result = dict(round_value)
    if surface:
        if surface not in result["required_surfaces"]:
            raise ReviewRoundError(f"Unknown required surface: {surface}")
        result["surface_decisions"] = [
            {**item, "status": "approved"} if item["surface"] == surface else item
            for item in result["surface_decisions"]
        ]
    if journey:
        if journey not in result["required_journeys"]:
            raise ReviewRoundError(f"Unknown required journey: {journey}")
        result["journey_decisions"] = [
            {**item, "status": "approved"} if item["journey"] == journey else item
            for item in result["journey_decisions"]
        ]
    errors = validate_document(result, "review-round")
    if errors:
        raise ReviewRoundError("Review Round invalid after approval: " + "; ".join(errors))
    return result


def finalize_round(
    round_value: dict[str, Any],
    feedback_values: list[dict[str, Any]],
) -> dict[str, Any]:
    unresolved = [
        item["feedback_id"] for item in feedback_values
        if item.get("status") not in {"resolved", "accepted", "rejected"}
    ]
    if unresolved:
        raise ReviewRoundError("Unresolved feedback: " + ", ".join(unresolved))
    surface_blockers = [
        item["surface"] for item in round_value["surface_decisions"]
        if item["status"] != "approved"
    ]
    journey_blockers = [
        item["journey"] for item in round_value["journey_decisions"]
        if item["status"] != "approved"
    ]
    if surface_blockers or journey_blockers:
        result = {**round_value, "outcome": "changes-requested"}
    else:
        if not round_value.get("qa_refs"):
            raise ReviewRoundError("An approved Review Round requires QA evidence")
        result = {**round_value, "outcome": "approved"}
    errors = validate_document(result, "review-round")
    if errors:
        raise ReviewRoundError("Final Review Round invalid: " + "; ".join(errors))
    return result



def link_next_revision(
    round_value: dict[str, Any],
    next_revision_ref: str,
) -> dict[str, Any]:
    if round_value.get("outcome") not in {"changes-requested", "in-review"}:
        raise ReviewRoundError(
            "Next Prototype Revision can only be linked from an active/changes-requested round"
        )
    result = {**round_value, "next_revision_ref": next_revision_ref}
    errors = validate_document(result, "review-round")
    if errors:
        raise ReviewRoundError("Review Round invalid after next-revision link: " + "; ".join(errors))
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description="Govern Prototype Revisions and Review Rounds")
    sub = parser.add_subparsers(dest="command", required=True)

    revision = sub.add_parser("create-revision")
    revision.add_argument("--client", required=True)
    revision.add_argument("--review", required=True)
    revision.add_argument("--sequence", type=int, required=True)
    revision.add_argument("--created-by", required=True)
    revision.add_argument("--created-at")
    revision.add_argument("--parent-revision-ref")

    round_cmd = sub.add_parser("create-round")
    round_cmd.add_argument("--client", required=True)
    round_cmd.add_argument("--revision", required=True)
    round_cmd.add_argument("--review", required=True)
    round_cmd.add_argument("--sequence", type=int, required=True)
    round_cmd.add_argument("--previous-round-ref")

    add = sub.add_parser("add-feedback")
    add.add_argument("round_path", type=Path)
    add.add_argument("--surface", required=True)
    add.add_argument("--journey")
    add.add_argument("--screen")
    add.add_argument("--component")
    add.add_argument("--type", dest="feedback_type", required=True,
                     choices=sorted(MATERIAL_TYPES | MINOR_TYPES | {"other"}))
    add.add_argument("--comment", required=True)
    add.add_argument("--action", required=True,
                     choices=["request-change", "approve", "discuss"])
    add.add_argument("--evidence-ref")
    add.add_argument("--created-by")
    add.add_argument("--created-at")

    route = sub.add_parser("route-feedback")
    route.add_argument("round_path", type=Path)
    route.add_argument("feedback_path", type=Path)
    route.add_argument("--live-review-ref")
    route.add_argument("--change-contract-ref")

    resolve = sub.add_parser("resolve-feedback")
    resolve.add_argument("feedback_path", type=Path)

    qa = sub.add_parser("record-qa")
    qa.add_argument("round_path", type=Path)
    qa.add_argument("--qa-ref", action="append", required=True)

    approve = sub.add_parser("approve")
    approve.add_argument("round_path", type=Path)
    approve.add_argument("--surface")
    approve.add_argument("--journey")

    finalize = sub.add_parser("finalize")
    finalize.add_argument("round_path", type=Path)

    link = sub.add_parser("link-next")
    link.add_argument("round_path", type=Path)
    link.add_argument("--next-revision-ref", required=True)

    args = parser.parse_args()
    try:
        if args.command == "create-revision":
            value = create_prototype_revision(
                args.client,
                review_file=args.review,
                sequence=args.sequence,
                created_by=args.created_by,
                parent_revision_ref=args.parent_revision_ref,
                created_at=args.created_at,
            )
            path = ROOT / "client-projects" / args.client / "experience" / "revisions" / f"{value['revision_id']}.yaml"
            if path.exists():
                raise ReviewRoundError(f"Refusing to overwrite immutable revision: {path}")
            save_yaml(path, value)
            review_path = ROOT / "client-projects" / args.client / "feedback" / args.review
            review_value = load_yaml(review_path)
            review_value["prototype_revision_ref"] = f"experience/revisions/{path.name}"
            errors = validate_document(review_value, "review-session")
            if errors:
                raise ReviewRoundError("Review Session invalid after revision bind: " + "; ".join(errors))
            save_yaml(review_path, review_value)
            print(path.relative_to(ROOT))
            return 0
        if args.command == "create-round":
            value = create_review_round(
                args.client,
                revision_file=args.revision,
                review_file=args.review,
                sequence=args.sequence,
                previous_round_ref=args.previous_round_ref,
            )
            path = ROOT / "client-projects" / args.client / "feedback" / "rounds" / f"{value['round_id']}.yaml"
            if path.exists():
                raise ReviewRoundError(f"Refusing to overwrite Review Round: {path}")
            save_yaml(path, value)
            review_path = ROOT / "client-projects" / args.client / "feedback" / args.review
            review_value = load_yaml(review_path)
            review_value["review_round_ref"] = f"feedback/rounds/{path.name}"
            errors = validate_document(review_value, "review-session")
            if errors:
                raise ReviewRoundError("Review Session invalid after round bind: " + "; ".join(errors))
            save_yaml(review_path, review_value)
            print(path.relative_to(ROOT))
            return 0
        if args.command == "add-feedback":
            round_value = load_yaml(args.round_path)
            updated, feedback = add_feedback(
                round_value,
                surface=args.surface,
                journey=args.journey,
                screen=args.screen,
                component=args.component,
                feedback_type=args.feedback_type,
                comment=args.comment,
                action=args.action,
                evidence_ref=args.evidence_ref,
                created_by=args.created_by,
                created_at=args.created_at,
            )
            feedback_path = args.round_path.parents[1] / "items" / f"{feedback['feedback_id']}.yaml"
            save_yaml(feedback_path, feedback)
            save_yaml(args.round_path, updated)
            print(feedback_path)
            return 0
        if args.command == "route-feedback":
            updated_round, updated_feedback = route_feedback(
                load_yaml(args.round_path),
                load_yaml(args.feedback_path),
                live_review_ref=args.live_review_ref,
                change_contract_ref=args.change_contract_ref,
            )
            save_yaml(args.feedback_path, updated_feedback)
            save_yaml(args.round_path, updated_round)
            print(args.feedback_path)
            return 0
        if args.command == "resolve-feedback":
            save_yaml(args.feedback_path, resolve_feedback(load_yaml(args.feedback_path)))
            print(args.feedback_path)
            return 0
        if args.command == "record-qa":
            save_yaml(args.round_path, record_qa(load_yaml(args.round_path), args.qa_ref))
            print(args.round_path)
            return 0
        if args.command == "approve":
            save_yaml(
                args.round_path,
                approve_target(load_yaml(args.round_path), surface=args.surface, journey=args.journey),
            )
            print(args.round_path)
            return 0
        if args.command == "link-next":
            save_yaml(
                args.round_path,
                link_next_revision(load_yaml(args.round_path), args.next_revision_ref),
            )
            print(args.round_path)
            return 0
        if args.command == "finalize":
            round_value = load_yaml(args.round_path)
            feedback_values = []
            for ref in round_value.get("feedback_refs", []):
                relative = ref if ref.startswith("feedback/") else f"feedback/{ref}"
                feedback_values.append(
                    load_yaml(ROOT / "client-projects" / round_value["client_id"] / relative)
                )
            save_yaml(args.round_path, finalize_round(round_value, feedback_values))
            print(args.round_path)
            return 0
        return 2
    except ReviewRoundError as exc:
        print(f"review-round-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
