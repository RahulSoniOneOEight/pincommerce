from __future__ import annotations

from typing import Any

ALLOWED_SEVERITIES = {"info", "minor", "major", "critical"}


def normalize_review(review: dict[str, Any]) -> dict[str, Any]:
    if not review.get("provider"):
        raise ValueError("visual QA provider is required")
    if not review.get("screenshot_sha256"):
        raise ValueError("visual QA must reference screenshot evidence")
    findings = []
    for item in review.get("findings", []):
        severity = str(item.get("severity", "info"))
        if severity not in ALLOWED_SEVERITIES:
            raise ValueError(f"Unsupported visual QA severity: {severity}")
        findings.append({
            "severity": severity,
            "category": str(item.get("category", "visual")),
            "message": str(item.get("message", "")),
            "evidence": list(item.get("evidence", [])),
        })
    critical = sum(1 for x in findings if x["severity"] == "critical")
    major = sum(1 for x in findings if x["severity"] == "major")
    return {
        "provider": str(review["provider"]),
        "model": review.get("model"),
        "screenshot_sha256": str(review["screenshot_sha256"]),
        "findings": findings,
        "status": "blocked" if critical else "review" if major else "advisory-pass",
        "approval_authority": False,
        "rule": "Visual AI is advisory evidence and cannot independently approve or promote reusable UI",
    }
