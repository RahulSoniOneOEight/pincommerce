from __future__ import annotations

from typing import Any

from tooling.contracts.validator import validate_document


def evaluate_health(component_rows:list[dict[str,Any]])->dict[str,Any]:
    normalized=[]
    for row in component_rows:
        license_state=row.get("license","unknown")
        maintenance=row.get("maintenance","unknown")
        security=row.get("security","unknown")
        if "blocked" in {license_state,security} or maintenance=="stale":
            eligibility="blocked"
        elif "review" in {license_state,security} or maintenance in {"watch","unknown"}:
            eligibility="review"
        else:
            eligibility="eligible"
        normalized.append({
            "id":row["id"],
            "license":license_state,
            "maintenance":maintenance,
            "security":security,
            "eligibility":eligibility,
            **{k:v for k,v in row.items() if k not in {"id","license","maintenance","security"}},
        })
    status="blocked" if any(x["eligibility"]=="blocked" for x in normalized) else "review" if any(x["eligibility"]=="review" for x in normalized) else "passed"
    result={"health_id":"DHEALTH-current","components":normalized,"status":status}
    errors=validate_document(result,"design-health")
    if errors:
        raise ValueError("; ".join(errors))
    return result
