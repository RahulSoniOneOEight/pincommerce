from __future__ import annotations

from typing import Any


def evaluate_promotion(
    *,
    dependency: dict[str, Any],
    quality: dict[str, Any],
    visual: dict[str, Any],
    impact: dict[str, Any],
    human_approval: dict[str, Any] | None,
) -> dict[str, Any]:
    blockers = []
    if dependency.get("eligibility") != "eligible":
        blockers.append("dependency-not-eligible")
    if quality.get("status") not in {"review-ready", "approved"}:
        blockers.append("quality-not-review-ready")
    if visual.get("status") != "passed":
        blockers.append("visual-evidence-not-passed")
    if impact.get("count", 0) and not impact.get("reviewed", False):
        blockers.append("affected-clients-not-reviewed")
    if not human_approval or not human_approval.get("approved") or not human_approval.get("reviewer"):
        blockers.append("human-approval-required")
    return {
        "status": "promotable" if not blockers else "blocked",
        "blocking_items": blockers,
        "rule": "shared component promotion requires deterministic evidence, impact review and explicit human approval",
    }
