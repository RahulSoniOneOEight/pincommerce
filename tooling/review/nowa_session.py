from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document
from tooling.validation.identifiers import IdentifierError, validate_identifier

ROOT = Path(__file__).resolve().parents[2]

MINOR_CATEGORIES = {
    "spacing",
    "layout",
    "typography",
    "content",
    "component-style",
    "navigation-presentation",
}
MATERIAL_CATEGORIES = {
    "business-rule",
    "integration",
    "data",
    "security",
    "architecture",
    "permission",
    "financial",
    "state-machine",
    "workflow",
}


class NowaReviewError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise NowaReviewError(f"Missing live review input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise NowaReviewError(f"Expected mapping in {path}")
    return value


def save_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def classify_edit(category: str) -> tuple[str, str]:
    if category in MINOR_CATEGORIES:
        return "minor-live", "apply-in-nowa"
    if category in MATERIAL_CATEGORIES:
        return "material-change", "change-contract"
    raise NowaReviewError(f"Unknown live-review category: {category}")


def create_live_session(
    client_id: str,
    review_id: str,
    source_build_id: str,
    started_by: str,
    participants: list[str],
    sequence: str = "001",
) -> dict[str, Any]:
    for value, kind in [
        (client_id, "client_id"),
        (review_id, "review_id"),
        (source_build_id, "source_build_id"),
        (sequence, "sequence"),
    ]:
        try:
            validate_identifier(value, kind=kind)
        except IdentifierError as exc:
            raise NowaReviewError(str(exc)) from exc

    session = {
        "session_id": f"LIVE-{client_id}-NOWA-{sequence}",
        "client_id": client_id,
        "review_id": review_id,
        "source_build_id": source_build_id,
        "tool": "nowa",
        "started_by": started_by,
        "started_at": None,
        "participants": list(dict.fromkeys(participants or [started_by])),
        "edits": [],
        "resulting_revision": None,
        "visual_qa_refs": [],
        "client_confirmed_by": None,
        "client_confirmed_at": None,
        "status": "planned",
        "notes": [
            "Nowa is permitted for minor visual/UX edits only.",
            "Material business/data/integration/security/architecture changes must route to Change Contract.",
        ],
    }
    errors = validate_document(session, "live-review-session")
    if errors:
        raise NowaReviewError("Generated live review session invalid: " + "; ".join(errors))
    return session


def add_edit(
    session: dict[str, Any],
    *,
    category: str,
    summary: str,
    surface: str,
    target: str,
    before: str | None = None,
    after: str | None = None,
    git_paths: list[str] | None = None,
) -> dict[str, Any]:
    classification, route = classify_edit(category)
    edits = list(session.get("edits", []))
    edit_id = f"EDIT-{len(edits)+1:04d}"
    edit = {
        "edit_id": edit_id,
        "category": category,
        "summary": summary,
        "surface": surface,
        "target": target,
        "before": before,
        "after": after,
        "classification": classification,
        "route": route,
        "status": "proposed",
        "git_paths": git_paths or [],
        "git_diff_ref": None,
        "resulting_revision": None,
        "change_contract_ref": None,
        "qa_required": True,
        "client_confirmed": False,
    }
    edits.append(edit)
    result = {**session, "edits": edits, "status": "live"}
    errors = validate_document(result, "live-review-session")
    if errors:
        raise NowaReviewError("Live review edit invalid: " + "; ".join(errors))
    return result


def apply_minor_edit(
    session: dict[str, Any],
    edit_id: str,
    *,
    git_diff_ref: str,
    resulting_revision: str,
) -> dict[str, Any]:
    edits = []
    found = False
    for edit in session.get("edits", []):
        item = dict(edit)
        if item["edit_id"] == edit_id:
            found = True
            if item["classification"] != "minor-live" or item["route"] != "apply-in-nowa":
                raise NowaReviewError(
                    f"{edit_id} is material and cannot be applied as a live Nowa change"
                )
            item["status"] = "applied"
            item["git_diff_ref"] = git_diff_ref
            item["resulting_revision"] = resulting_revision
        edits.append(item)
    if not found:
        raise NowaReviewError(f"Unknown edit_id: {edit_id}")
    result = {
        **session,
        "edits": edits,
        "resulting_revision": resulting_revision,
        "status": "qa-required",
    }
    errors = validate_document(result, "live-review-session")
    if errors:
        raise NowaReviewError("Applied live review session invalid: " + "; ".join(errors))
    return result


def route_material_edit(
    session: dict[str, Any],
    edit_id: str,
    change_contract_ref: str,
) -> dict[str, Any]:
    edits = []
    found = False
    for edit in session.get("edits", []):
        item = dict(edit)
        if item["edit_id"] == edit_id:
            found = True
            if item["classification"] != "material-change":
                raise NowaReviewError(f"{edit_id} is minor and does not require Change Contract")
            item["status"] = "change-contract-created"
            item["change_contract_ref"] = change_contract_ref
        edits.append(item)
    if not found:
        raise NowaReviewError(f"Unknown edit_id: {edit_id}")
    result = {**session, "edits": edits}
    errors = validate_document(result, "live-review-session")
    if errors:
        raise NowaReviewError("Material-route session invalid: " + "; ".join(errors))
    return result


def record_qa(
    session: dict[str, Any],
    visual_qa_refs: list[str],
) -> dict[str, Any]:
    if not visual_qa_refs:
        raise NowaReviewError("At least one Visual QA reference is required")
    pending_minor = [
        edit["edit_id"] for edit in session.get("edits", [])
        if edit["classification"] == "minor-live" and edit["status"] != "applied"
    ]
    if pending_minor:
        raise NowaReviewError(
            "Minor live edits must be applied or rejected before QA: " + ", ".join(pending_minor)
        )
    edits = []
    for edit in session.get("edits", []):
        item = dict(edit)
        if item["classification"] == "minor-live" and item["status"] == "applied":
            item["status"] = "qa-passed"
        edits.append(item)
    result = {
        **session,
        "edits": edits,
        "visual_qa_refs": visual_qa_refs,
        "status": "qa-passed",
    }
    errors = validate_document(result, "live-review-session")
    if errors:
        raise NowaReviewError("QA-completed session invalid: " + "; ".join(errors))
    return result


def client_confirm(
    session: dict[str, Any],
    confirmed_by: str,
    confirmed_at: str,
) -> dict[str, Any]:
    if session.get("status") != "qa-passed":
        raise NowaReviewError("Client confirmation requires post-Nowa QA to pass first")
    result = {
        **session,
        "client_confirmed_by": confirmed_by,
        "client_confirmed_at": confirmed_at,
        "status": "client-confirmed",
    }
    edits = []
    for edit in result.get("edits", []):
        item = dict(edit)
        if item["classification"] == "minor-live" and item["status"] == "qa-passed":
            item["client_confirmed"] = True
        edits.append(item)
    result["edits"] = edits
    errors = validate_document(result, "live-review-session")
    if errors:
        raise NowaReviewError("Client-confirmed session invalid: " + "; ".join(errors))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Govern Nowa live client-review sessions for minor Flutter refinements"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--client", required=True)
    create.add_argument("--review-id", required=True)
    create.add_argument("--build-id", required=True)
    create.add_argument("--started-by", required=True)
    create.add_argument("--participant", action="append", default=[])
    create.add_argument("--sequence", default="001")
    create.add_argument("--output", type=Path, required=True)

    add = sub.add_parser("add-edit")
    add.add_argument("path", type=Path)
    add.add_argument("--category", required=True)
    add.add_argument("--summary", required=True)
    add.add_argument("--surface", required=True)
    add.add_argument("--target", required=True)
    add.add_argument("--before")
    add.add_argument("--after")
    add.add_argument("--git-path", action="append", default=[])

    apply_cmd = sub.add_parser("apply-minor")
    apply_cmd.add_argument("path", type=Path)
    apply_cmd.add_argument("--edit-id", required=True)
    apply_cmd.add_argument("--git-diff-ref", required=True)
    apply_cmd.add_argument("--resulting-revision", required=True)

    route_cmd = sub.add_parser("route-material")
    route_cmd.add_argument("path", type=Path)
    route_cmd.add_argument("--edit-id", required=True)
    route_cmd.add_argument("--change-contract-ref", required=True)

    qa_cmd = sub.add_parser("record-qa")
    qa_cmd.add_argument("path", type=Path)
    qa_cmd.add_argument("--visual-qa-ref", action="append", required=True)

    confirm_cmd = sub.add_parser("confirm")
    confirm_cmd.add_argument("path", type=Path)
    confirm_cmd.add_argument("--confirmed-by", required=True)
    confirm_cmd.add_argument("--confirmed-at", required=True)

    args = parser.parse_args()
    try:
        if args.command == "create":
            value = create_live_session(
                args.client, args.review_id, args.build_id, args.started_by,
                args.participant or [args.started_by], args.sequence
            )
            save_yaml(args.output, value)
            print(args.output)
            return 0
        if args.command == "add-edit":
            value = load_yaml(args.path)
            value = add_edit(
                value,
                category=args.category,
                summary=args.summary,
                surface=args.surface,
                target=args.target,
                before=args.before,
                after=args.after,
                git_paths=args.git_path,
            )
            save_yaml(args.path, value)
            print(yaml.safe_dump(value["edits"][-1], sort_keys=False))
            return 0
        if args.command == "apply-minor":
            value = apply_minor_edit(
                load_yaml(args.path),
                args.edit_id,
                git_diff_ref=args.git_diff_ref,
                resulting_revision=args.resulting_revision,
            )
            save_yaml(args.path, value)
            print(args.path)
            return 0
        if args.command == "route-material":
            value = route_material_edit(
                load_yaml(args.path), args.edit_id, args.change_contract_ref
            )
            save_yaml(args.path, value)
            print(args.path)
            return 0
        if args.command == "record-qa":
            value = record_qa(load_yaml(args.path), args.visual_qa_ref)
            save_yaml(args.path, value)
            print(args.path)
            return 0
        if args.command == "confirm":
            value = client_confirm(
                load_yaml(args.path), args.confirmed_by, args.confirmed_at
            )
            save_yaml(args.path, value)
            print(args.path)
            return 0
        return 2
    except NowaReviewError as exc:
        print(f"nowa-review-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
