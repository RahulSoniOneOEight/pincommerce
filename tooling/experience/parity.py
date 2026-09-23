from __future__ import annotations

from typing import Any


def compare_pattern_parity(flutter: dict[str,Any], web: dict[str,Any]) -> dict[str,Any]:
    semantic_fields={"states","actions","data_fields","error_states"}
    mismatches=[]
    for field in sorted(semantic_fields):
        left=set(flutter.get(field,[]))
        right=set(web.get(field,[]))
        if left!=right:
            mismatches.append({
                "field":field,
                "flutter_only":sorted(left-right),
                "web_only":sorted(right-left),
            })
    return {
        "status":"passed" if not mismatches else "review",
        "mismatches":mismatches,
        "rule":"behavioral parity required; platform-native presentation differences allowed",
    }
