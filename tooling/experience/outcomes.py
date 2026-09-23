from __future__ import annotations

from collections import defaultdict
from typing import Any


def summarize_outcomes(records:list[dict[str,Any]])->dict[str,Any]:
    by_target=defaultdict(lambda:{"accepted":0,"accepted-with-changes":0,"rejected":0})
    for record in records:
        decision=record.get("decision","unknown")
        if decision in by_target[record.get("target","unknown")]:
            by_target[record.get("target","unknown")][decision]+=1
    return {
        "targets":dict(sorted(by_target.items())),
        "rule":"historical outcomes inform candidate ranking but never override current client requirements or human approval",
    }
