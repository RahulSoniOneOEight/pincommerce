from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.validation.identifiers import IdentifierError, validate_identifier
from tooling.experience.coverage import CoverageError, assert_client_review_ready
from tooling.prototype.core_runtime import (
    CoreRuntimeError,
    assert_core_runtime_ready,
    client_requires_core_runtime,
)

ROOT = Path(__file__).resolve().parents[2]


class ReviewError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ReviewError(f"Missing review input: {path}")
    with path.open("r", encoding="utf-8") as fh:
        value = yaml.safe_load(fh)
    if not isinstance(value, dict):
        raise ReviewError(f"Expected mapping in {path}")
    return value


def save_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(value, fh, sort_keys=False)


def create_build_identity(
    client_id: str,
    direction_file: str,
    source_revision: str,
    created_by: str,
    environment: str = "prototype",
    root: Path = ROOT,
) -> dict[str, Any]:
    try:
        validate_identifier(client_id, kind="client_id")
        validate_identifier(direction_file, kind="direction filename")
        validate_identifier(source_revision, kind="source_revision")
    except IdentifierError as exc:
        raise ReviewError(str(exc)) from exc

    project = root / "client-projects" / client_id
    direction = load_yaml(project / "experience" / "directions" / direction_file)
    direction_id = direction["direction_id"]
    suffix = direction_id.split("-")[-1].lower()
    build_id = f"BLD-{client_id}-{suffix}-{source_revision[:12]}"
    return {
        "build_id": build_id,
        "client_id": client_id,
        "direction_id": direction_id,
        "source_revision": source_revision,
        "environment": environment,
        "surfaces": list(direction["surfaces"]),
        "created_by": created_by,
        "immutable": True,
    }


def create_capture_manifest(
    build: dict[str, Any],
    states: list[str],
) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    for surface in build["surfaces"]:
        runtime = (
            "flutter" if surface == "customer-app"
            else "external" if surface in {"erp", "warehouse", "customer-support"}
            else "web"
        )
        viewports = ["390x844"] if runtime == "flutter" else ["1440x1024", "390x844"]
        if runtime == "external":
            viewports = ["external"]
        for viewport in viewports:
            for state in states:
                targets.append({
                    "surface": surface,
                    "runtime": runtime,
                    "viewport": viewport,
                    "state": state,
                    "output": f"review/artifacts/{build['build_id']}/{surface}/{viewport}/{state}.png",
                })

    return {
        "capture_id": f"CAP-{build['build_id']}",
        "client_id": build["client_id"],
        "build_id": build["build_id"],
        "direction_id": build["direction_id"],
        "targets": targets,
        "status": "planned",
    }


def create_review_session(
    build: dict[str, Any],
    capture: dict[str, Any],
) -> dict[str, Any]:
    artifacts = []
    for index, target in enumerate(capture["targets"], start=1):
        artifacts.append({
            "artifact_id": f"ART-{index:04d}",
            "surface": target["surface"],
            "route_or_screen": target["state"],
            "environment": build["environment"],
            "build_identity": build["build_id"],
            "journey": "",
            "viewport": target["viewport"],
            "preview_url": "",
            "screenshot_ref": target["output"],
            "approval_status": "pending",
        })
    return {
        "review_id": f"REV-{build['build_id']}",
        "client_id": build["client_id"],
        "build_id": build["build_id"],
        "direction_id": build["direction_id"],
        "artifacts": artifacts,
        "status": "draft",
    }


def write_review_bundle(
    client_id: str,
    direction_file: str,
    source_revision: str,
    created_by: str,
    root: Path = ROOT,
) -> list[Path]:
    try:
        assert_client_review_ready(client_id, direction_file, root)
    except CoverageError as exc:
        raise ReviewError(
            "Client review blocked by prototype completeness gate: " + str(exc)
        ) from exc

    if client_requires_core_runtime(client_id, root):
        try:
            assert_core_runtime_ready(client_id, root)
        except CoreRuntimeError as exc:
            raise ReviewError(
                "Client review blocked by functional core-runtime gate: " + str(exc)
            ) from exc

    build = create_build_identity(client_id, direction_file, source_revision, created_by, root=root)
    fixture = load_yaml(root / "client-projects" / client_id / "experience" / "fixtures" / "commerce-baseline.yaml")
    states = [item["id"] for item in fixture["states"]]
    capture = create_capture_manifest(build, states)
    review = create_review_session(build, capture)

    project = root / "client-projects" / client_id
    paths = [
        project / "experience" / "builds" / f"{build['build_id']}.yaml",
        project / "experience" / "visual-qa" / f"{capture['capture_id']}.yaml",
        project / "feedback" / f"{review['review_id']}.yaml",
    ]
    for path, value in zip(paths, (build, capture, review), strict=True):
        if path.exists():
            raise ReviewError(f"Refusing to overwrite existing review artifact: {path}")
        save_yaml(path, value)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Create build/capture/review bundle")
    parser.add_argument("--client", required=True)
    parser.add_argument("--direction", default="a.yaml")
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--created-by", required=True)
    args = parser.parse_args()

    try:
        paths = write_review_bundle(
            args.client,
            args.direction,
            args.source_revision,
            args.created_by,
        )
        for path in paths:
            print(path.relative_to(ROOT))
        return 0
    except ReviewError as exc:
        print(f"review-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
