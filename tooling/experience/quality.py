from __future__ import annotations

from typing import Any

from tooling.contracts.validator import validate_document


class DesignQualityError(ValueError):
    pass


def evaluate_quality(
    *,
    client_id: str,
    target: str,
    scores: dict[str, tuple[float, list[str], bool]],
    weights: dict[str, float],
    threshold: float = 80,
    winner_of: str | None = None,
) -> dict[str, Any]:
    missing = sorted(set(weights) - set(scores))
    if missing:
        raise DesignQualityError(f"Missing quality criteria: {missing}")
    total_weight = sum(float(v) for v in weights.values())
    if total_weight <= 0:
        raise DesignQualityError("Quality weights must sum above zero")

    criteria = []
    weighted = 0.0
    deterministic_count = 0
    for criterion, weight in weights.items():
        score, evidence, deterministic = scores[criterion]
        if score < 0 or score > 100:
            raise DesignQualityError(f"Invalid score for {criterion}: {score}")
        if not evidence:
            raise DesignQualityError(f"Evidence required for {criterion}")
        weighted += float(score) * float(weight)
        deterministic_count += int(bool(deterministic))
        criteria.append({
            "id": criterion,
            "weight": float(weight),
            "score": float(score),
            "evidence": list(evidence),
            "deterministic": bool(deterministic),
        })

    final_score = round(weighted / total_weight, 2)
    # An AI-only visual opinion cannot approve a reusable component. At least one
    # deterministic criterion must be present; final approval still belongs to
    # the governed review process.
    if deterministic_count == 0:
        status = "failed"
    elif final_score >= threshold:
        status = "review-ready"
    else:
        status = "failed"

    result = {
        "evaluation_id": f"DQ-{client_id}-{target}".replace("/", "-"),
        "client_id": client_id,
        "target": target,
        "criteria": criteria,
        "score": final_score,
        "threshold": float(threshold),
        "status": status,
        "winner_of": winner_of,
    }
    errors = validate_document(result, "design-quality-evaluation")
    if errors:
        raise DesignQualityError("Invalid quality evaluation: " + "; ".join(errors))
    return result


def select_tournament_winner(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [item for item in evaluations if item.get("status") in {"review-ready", "approved"}]
    if not eligible:
        raise DesignQualityError("No eligible design candidate")
    # Deterministic tie-break: highest quality score, then target id.
    return sorted(eligible, key=lambda item: (-float(item["score"]), str(item["target"])))[0]
