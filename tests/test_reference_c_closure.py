from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from tooling.review.freeze import FreezeError, build_scope_baseline, write_scope_baseline
from tooling.review.review_round import (
    add_feedback,
    approve_target,
    create_prototype_revision,
    create_review_round,
    finalize_round,
    link_next_revision,
    record_qa,
    resolve_feedback,
    route_feedback,
)
from tooling.review.visual_qa import REQUIRED_CHECKS
from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[1]
CLIENT_ID = "reference-retail"
SURFACES = ["customer-app", "web-store", "commerce-admin", "analytics", "erp"]
JOURNEYS = [
    "browse-to-buy", "search-to-buy", "order-tracking", "return-refund",
    "quote-to-order", "repeat-order", "credit-order",
]


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def build_record(build_id: str, source_revision: str) -> dict:
    return {
        "build_id": build_id,
        "client_id": CLIENT_ID,
        "direction_id": "DIR-REFERENCE-RETAIL-A",
        "source_revision": source_revision,
        "environment": "prototype",
        "surfaces": SURFACES,
        "created_by": "reference-acceptance",
        "immutable": True,
    }


def review_record(build_id: str) -> dict:
    return {
        "review_id": f"REV-{build_id}",
        "client_id": CLIENT_ID,
        "build_id": build_id,
        "direction_id": "DIR-REFERENCE-RETAIL-A",
        "coverage_ref": "experience/prototypes/a-coverage.yaml",
        "implementation_ref": "experience/prototypes/a-implementation.yaml",
        "core_runtime_ref": "experience/prototype-core-runtime.yaml",
        "demo_dataset_ref": "experience/fixtures/reference-retail-demo-dataset.yaml",
        "prototype_revision_ref": None,
        "review_round_ref": None,
        "surface_approvals": [{"surface": x, "status": "pending"} for x in SURFACES],
        "journey_approvals": [{"journey": x, "status": "pending"} for x in JOURNEYS],
        "artifacts": [
            {
                "artifact_id": f"ART-{i:02d}",
                "surface": surface,
                "route_or_screen": "default",
                "environment": "prototype",
                "build_identity": build_id,
                "journey": JOURNEYS[0],
                "viewport": "reference",
                "preview_url": "",
                "screenshot_ref": f"review/artifacts/{build_id}/{surface}/default.png",
                "approval_status": "pending",
            }
            for i, surface in enumerate(SURFACES, start=1)
        ],
        "status": "draft",
    }


def qa_record(build_id: str, surface: str) -> dict:
    return {
        "qa_id": f"VQA-{build_id}-{surface}",
        "client_id": CLIENT_ID,
        "direction_id": "DIR-REFERENCE-RETAIL-A",
        "surface": surface,
        "build_identity": build_id,
        "checks": [
            {
                "id": check,
                "status": "pass",
                "evidence": f"reference-acceptance:{surface}:{check}",
                "notes": [],
            }
            for check in REQUIRED_CHECKS
        ],
        "status": "passed",
    }


class ReferenceFinalCClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        src = ROOT / "client-projects" / CLIENT_ID
        dst = self.root / "client-projects" / CLIENT_ID
        shutil.copytree(src, dst)
        self.project = dst
        for relative in (
            "experience/builds", "experience/revisions", "experience/visual-qa",
            "feedback/rounds", "feedback/items",
        ):
            (self.project / relative).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp.cleanup()

    def _write_review_and_build(self, build_id: str, source_revision: str) -> str:
        dump(self.project / "experience" / "builds" / f"{build_id}.yaml", build_record(build_id, source_revision))
        review = review_record(build_id)
        review_file = f"{review['review_id']}.yaml"
        dump(self.project / "feedback" / review_file, review)
        return review_file

    def _bind_review(self, review_file: str, revision_ref: str, round_ref: str, *, approved: bool) -> None:
        path = self.project / "feedback" / review_file
        review = yaml.safe_load(path.read_text(encoding="utf-8"))
        review["prototype_revision_ref"] = revision_ref
        review["review_round_ref"] = round_ref
        if approved:
            review["status"] = "approved"
            review["surface_approvals"] = [
                {"surface": x, "status": "approved"} for x in SURFACES
            ]
            review["journey_approvals"] = [
                {"journey": x, "status": "approved"} for x in JOURNEYS
            ]
            for artifact in review["artifacts"]:
                artifact["approval_status"] = "approved"
        dump(path, review)
        self.assertEqual(validate_document(review, "review-session"), [])

    def test_two_round_reference_closure_writes_v2_without_mutating_legacy_v1(self):
        legacy = self.project / "approved" / "scope-baseline.yaml"
        legacy_before = legacy.read_text(encoding="utf-8")
        source = os.environ.get("GITHUB_SHA", "reference-acceptance")

        # Prototype Revision 001 / Review Round 001
        review1_file = self._write_review_and_build("BLD-reference-retail-a-final001", source + "-r1")
        rev1 = create_prototype_revision(
            CLIENT_ID,
            review_file=review1_file,
            sequence=1,
            created_by="reference-acceptance",
            created_at="2026-09-22T19:00:00Z",
            root=self.root,
        )
        rev1_path = self.project / "experience" / "revisions" / f"{rev1['revision_id']}.yaml"
        dump(rev1_path, rev1)
        round1 = create_review_round(
            CLIENT_ID,
            revision_file=rev1_path.name,
            review_file=review1_file,
            sequence=1,
            root=self.root,
        )

        # Minor visual feedback -> Nowa route.
        round1, minor = add_feedback(
            round1,
            surface="customer-app",
            journey="credit-order",
            screen="checkout",
            component="credit-limit-card",
            feedback_type="visual",
            comment="Move available credit above the payment options.",
            action="request-change",
            created_by="reference-client",
            created_at="2026-09-22T19:05:00Z",
        )
        round1, minor = route_feedback(
            round1, minor, live_review_ref="feedback/LIVE-reference-final-001.yaml"
        )
        minor = resolve_feedback(minor)
        dump(self.project / "feedback" / "items" / f"{minor['feedback_id']}.yaml", minor)

        # Material business feedback -> Change Contract route.
        round1, material = add_feedback(
            round1,
            surface="commerce-admin",
            journey="credit-order",
            screen="approval-status",
            feedback_type="business-rule",
            comment="Orders above two lakh require manager approval.",
            action="request-change",
            created_by="reference-client",
            created_at="2026-09-22T19:06:00Z",
        )
        round1, material = route_feedback(
            round1, material, change_contract_ref="changes/CHG-reference-final-001.yaml"
        )
        material = resolve_feedback(material)
        dump(self.project / "feedback" / "items" / f"{material['feedback_id']}.yaml", material)

        round1 = finalize_round(round1, [minor, material])
        self.assertEqual(round1["outcome"], "changes-requested")
        round1_path = self.project / "feedback" / "rounds" / f"{round1['round_id']}.yaml"
        dump(round1_path, round1)
        self._bind_review(
            review1_file,
            f"experience/revisions/{rev1_path.name}",
            f"feedback/rounds/{round1_path.name}",
            approved=False,
        )

        # Prototype Revision 002 / Review Round 002.
        review2_file = self._write_review_and_build("BLD-reference-retail-a-final002", source + "-r2")
        rev2 = create_prototype_revision(
            CLIENT_ID,
            review_file=review2_file,
            sequence=2,
            created_by="reference-acceptance",
            parent_revision_ref=f"experience/revisions/{rev1_path.name}",
            created_at="2026-09-22T19:30:00Z",
            root=self.root,
        )
        rev2["feedback_refs"] = [
            f"feedback/items/{minor['feedback_id']}.yaml",
            f"feedback/items/{material['feedback_id']}.yaml",
        ]
        rev2["change_refs"] = ["changes/CHG-reference-final-001.yaml"]
        rev2["status"] = "approved"
        rev2_path = self.project / "experience" / "revisions" / f"{rev2['revision_id']}.yaml"
        dump(rev2_path, rev2)

        round1 = link_next_revision(round1, f"experience/revisions/{rev2_path.name}")
        dump(round1_path, round1)

        round2 = create_review_round(
            CLIENT_ID,
            revision_file=rev2_path.name,
            review_file=review2_file,
            sequence=2,
            previous_round_ref=f"feedback/rounds/{round1_path.name}",
            root=self.root,
        )

        qa_names = []
        for surface in SURFACES:
            qa = qa_record("BLD-reference-retail-a-final002", surface)
            name = f"{qa['qa_id']}.yaml"
            dump(self.project / "experience" / "visual-qa" / name, qa)
            qa_names.append(name)
        round2 = record_qa(
            round2, [f"experience/visual-qa/{name}" for name in qa_names]
        )
        for surface in SURFACES:
            round2 = approve_target(round2, surface=surface)
        for journey in JOURNEYS:
            round2 = approve_target(round2, journey=journey)
        round2 = finalize_round(round2, [])
        self.assertEqual(round2["outcome"], "approved")
        round2_path = self.project / "feedback" / "rounds" / f"{round2['round_id']}.yaml"
        dump(round2_path, round2)

        self._bind_review(
            review2_file,
            f"experience/revisions/{rev2_path.name}",
            f"feedback/rounds/{round2_path.name}",
            approved=True,
        )

        baseline = build_scope_baseline(
            CLIENT_ID,
            review_file=review2_file,
            visual_qa_files=qa_names,
            approved_by="reference-acceptance",
            approved_at="2026-09-22T20:00:00Z",
            direction_file="a.yaml",
            version=2,
            root=self.root,
        )
        path = write_scope_baseline(CLIENT_ID, baseline, self.root)

        self.assertEqual(path.name, "BASE-reference-retail-v2.yaml")
        self.assertEqual(path.parent.name, "scope-baselines")
        self.assertEqual(legacy.read_text(encoding="utf-8"), legacy_before)

        current = yaml.safe_load(
            (self.project / "approved" / "current-scope.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(current["version"], 2)
        self.assertEqual(
            current["baseline_ref"],
            "approved/scope-baselines/BASE-reference-retail-v2.yaml",
        )
        self.assertEqual(validate_document(current, "current-scope"), [])
        self.assertEqual(validate_document(baseline, "scope-baseline"), [])
        self.assertEqual(
            baseline["prototype_revision_ref"],
            f"experience/revisions/{rev2_path.name}",
        )
        self.assertEqual(
            baseline["review_round_ref"],
            f"feedback/rounds/{round2_path.name}",
        )

        with self.assertRaises(FreezeError):
            write_scope_baseline(CLIENT_ID, baseline, self.root)


if __name__ == "__main__":
    unittest.main()
