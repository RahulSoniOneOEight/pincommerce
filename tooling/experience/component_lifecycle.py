from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

TRANSITIONS = {
    "candidate": {"evaluated"},
    "evaluated": {"approved", "candidate"},
    "approved": {"deprecated"},
    "deprecated": set(),
}


def transition(record: dict[str, Any], target: str, *, evidence: list[str], approver: str | None = None) -> dict[str, Any]:
    current = str(record.get("status", "candidate"))
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid lifecycle transition: {current}->{target}")
    if not evidence:
        raise ValueError("Lifecycle transition requires evidence")
    if target in {"approved", "deprecated"} and not approver:
        raise ValueError(f"{target} transition requires human approver")
    history = list(record.get("history", []))
    history.append({
        "from": current,
        "to": target,
        "evidence": list(evidence),
        "approver": approver,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })
    return {**record, "status": target, "history": history}
