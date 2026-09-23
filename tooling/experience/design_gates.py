from __future__ import annotations

import re
from pathlib import Path
from typing import Any

HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")


def state_completeness(required: list[str], implemented: list[str]) -> list[str]:
    return [f"missing-state:{state}" for state in required if state not in set(implemented)]


def semantic_token_violations(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if HEX.search(line) and "design-token-allow-raw" not in line:
                errors.append(f"{path}:{line_no}:raw-color")
    return errors


def accessibility_gate(record: dict[str, Any]) -> list[str]:
    required = {"keyboard","focus","semantics","contrast","reduced-motion"}
    passed = {item.get("id") for item in record.get("checks", []) if item.get("status") == "pass"}
    return [f"accessibility:{item}" for item in sorted(required - passed)]


def performance_gate(measurements: dict[str, float], budgets: dict[str, float]) -> list[str]:
    errors = []
    for metric, limit in budgets.items():
        if metric not in measurements:
            errors.append(f"performance:{metric}:missing")
        elif float(measurements[metric]) > float(limit):
            errors.append(f"performance:{metric}:{measurements[metric]}>{limit}")
    return errors


def component_ready(
    *,
    required_states: list[str],
    implemented_states: list[str],
    accessibility: dict[str, Any],
    measurements: dict[str, float],
    budgets: dict[str, float],
) -> dict[str, Any]:
    blockers = []
    blockers.extend(state_completeness(required_states, implemented_states))
    blockers.extend(accessibility_gate(accessibility))
    blockers.extend(performance_gate(measurements, budgets))
    return {"status":"passed" if not blockers else "blocked","blocking_items":blockers}
