from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "design-intelligence" / "stage2-policy.yaml"


def _load_policy() -> dict[str, Any]:
    value = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("stage2 policy must be a mapping")
    return value["learning"]


def build_learning_signals(
    outcomes: list[dict[str, Any]],
    telemetry: list[dict[str, Any]],
    *,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = policy or _load_policy()
    scores: dict[str, int] = defaultdict(int)
    observations: dict[str, int] = defaultdict(int)

    outcome_weights = {
        "accepted": int(cfg["accepted_weight"]),
        "accepted-with-changes": int(cfg["accepted_with_changes_weight"]),
        "rejected": int(cfg["rejected_weight"]),
    }
    telemetry_weights = {
        "passed": int(cfg["telemetry"]["passed_weight"]),
        "review": int(cfg["telemetry"]["review_weight"]),
        "failed": int(cfg["telemetry"]["failed_weight"]),
    }

    for record in outcomes:
        target = str(record.get("target", "unknown"))
        decision = str(record.get("decision", "unknown"))
        if decision in outcome_weights:
            scores[target] += outcome_weights[decision]
            observations[target] += 1

    for record in telemetry:
        target = str(record.get("target", "unknown"))
        status = str(record.get("status", "review"))
        if status in telemetry_weights:
            scores[target] += telemetry_weights[status]
            observations[target] += 1

    cap = int(cfg["max_ranking_adjustment"])
    minimum = int(cfg["minimum_observations"])
    signals = []
    for target in sorted(set(scores) | set(observations)):
        count = observations[target]
        raw = scores[target]
        adjustment = max(-cap, min(cap, raw)) if count >= minimum else 0
        signals.append({
            "target": target,
            "observations": count,
            "raw_signal": raw,
            "ranking_adjustment": adjustment,
            "eligible_for_learning": count >= minimum,
        })

    return {
        "signals": signals,
        "guardrails": dict(cfg["guardrails"]),
        "rule": "learning is advisory evidence only; current client requirements and human approval remain authoritative",
    }
