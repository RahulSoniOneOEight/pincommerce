from __future__ import annotations

from typing import Any, Iterable

DEFAULT_CHECKS = [
    "contract-validation",
    "unit-tests",
    "integration-tests",
    "e2e-critical-journeys",
    "security-secrets",
    "security-authz",
    "tenant-isolation",
    "dependency-vulnerability",
    "performance-budget",
    "accessibility",
    "migration-safety",
    "backup-recovery",
    "observability",
    "reconciliation",
    "provider-health",
]

VALID_STATUSES = {"pass", "fail", "warning", "not-run"}


class HardeningError(ValueError):
    pass


def _is_blocking(status: str, check_id: str, non_blocking: set[str]) -> bool:
    if status == "pass":
        return False
    if status == "warning":
        return check_id not in non_blocking
    # fail / not-run
    return True


def build_hardening_evidence(
    candidate_id: str,
    results: dict[str, tuple[str, str]],
    non_blocking: Iterable[str] = (),
) -> dict[str, Any]:
    """Build hardening evidence from per-check results.

    Policy: ``pass`` is acceptable; ``warning`` is blocking unless the check id is
    declared in ``non_blocking``; ``fail`` and ``not-run`` are always blocking.
    Unknown check ids and unknown statuses raise rather than being dropped.
    """
    non_blocking_set = set(non_blocking)
    unknown_checks = set(results) - set(DEFAULT_CHECKS)
    if unknown_checks:
        raise HardeningError(f"Unknown hardening check ids: {sorted(unknown_checks)}")

    checks = []
    blocking: list[str] = []
    for check_id in DEFAULT_CHECKS:
        status, evidence = results.get(check_id, ("not-run", ""))
        if status not in VALID_STATUSES:
            raise HardeningError(
                f"Unknown hardening status {status!r} for check {check_id!r}"
            )
        checks.append({
            "id": check_id,
            "status": status,
            "evidence": evidence,
            "notes": [],
        })
        if _is_blocking(status, check_id, non_blocking_set):
            blocking.append(check_id)

    return {
        "evidence_id": f"HARD-{candidate_id}",
        "candidate_id": candidate_id,
        "checks": checks,
        "non_blocking_checks": sorted(non_blocking_set),
        "status": "passed" if not blocking else "failed",
    }


def evaluate_hardening(
    evidence: dict[str, Any],
    non_blocking: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Re-evaluate a loaded hardening record under the strict blocking policy."""
    checks = evidence.get("checks", [])
    if not isinstance(checks, list):
        raise HardeningError("Hardening checks must be a list")

    if non_blocking is None:
        non_blocking_set = set(evidence.get("non_blocking_checks", []) or [])
    else:
        non_blocking_set = set(non_blocking)

    blocking: list[str] = []
    unknown: list[str] = []
    present: set[str] = set()
    for check in checks:
        check_id = check.get("id")
        status = check.get("status")
        if status not in VALID_STATUSES:
            raise HardeningError(
                f"Unknown hardening status {status!r} for check {check_id!r}"
            )
        present.add(str(check_id))
        if check_id not in DEFAULT_CHECKS:
            unknown.append(str(check_id))
            blocking.append(str(check_id))
            continue
        if _is_blocking(status, check_id, non_blocking_set):
            blocking.append(check_id)

    # A record that silently omits a required check must not pass: absent checks
    # are treated as ``not-run`` and are always blocking.
    missing = [check_id for check_id in DEFAULT_CHECKS if check_id not in present]
    blocking.extend(missing)

    return {
        "status": "passed" if not blocking else "failed",
        "blocking": blocking,
        "unknown_checks": unknown,
        "missing_checks": missing,
    }
