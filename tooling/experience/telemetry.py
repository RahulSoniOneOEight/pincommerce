from __future__ import annotations

from typing import Any


def evaluate_ux_metrics(metrics:dict[str,float], thresholds:dict[str,float])->dict[str,Any]:
    findings=[]
    for metric,threshold in thresholds.items():
        if metric not in metrics:
            findings.append({"metric":metric,"status":"missing"})
            continue
        value=float(metrics[metric])
        # threshold names ending _max are upper bounds; _min are lower bounds.
        if metric.endswith("_max"):
            status="pass" if value<=float(threshold) else "fail"
        elif metric.endswith("_min"):
            status="pass" if value>=float(threshold) else "fail"
        else:
            status="review"
        findings.append({"metric":metric,"value":value,"threshold":threshold,"status":status})
    return {
        "findings":findings,
        "status":"failed" if any(x["status"]=="fail" for x in findings) else "review" if any(x["status"] in {"missing","review"} for x in findings) else "passed",
        "rule":"production telemetry informs future selection but cannot silently change approved client design",
    }
