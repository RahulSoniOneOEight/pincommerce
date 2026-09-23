from __future__ import annotations

from pathlib import Path
from typing import Any

from tooling.experience.design_debt import scan


def build_report(root: Path) -> dict[str, Any]:
    result = scan(root)
    by_type: dict[str, int] = {}
    for finding in result["findings"]:
        kind = str(finding["type"])
        by_type[kind] = by_type.get(kind, 0) + 1
    return {**result, "by_type": dict(sorted(by_type.items()))}


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Design Debt Report",
        "",
        "Status: **" + str(report["status"]) + "**",
        "Findings: **" + str(report["finding_count"]) + "**",
        "",
    ]
    for kind, count in report.get("by_type", {}).items():
        lines.append("- " + str(kind) + ": " + str(count))
    if report.get("findings"):
        lines.extend(["", "## Findings"])
        for item in report["findings"]:
            detail = item.get("path") or ", ".join(item.get("families", []))
            lines.append("- " + str(item.get("type")) + " — " + str(detail))
    return "\n".join(lines) + "\n"


def to_html(report: dict[str, Any]) -> str:
    rows = []
    for item in report.get("findings", []):
        detail = item.get("path") or ", ".join(item.get("families", []))
        rows.append("<tr><td>" + str(item.get("type")) + "</td><td>" + str(detail) + "</td></tr>")
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Design Debt</title>"
        "<style>body{font-family:system-ui;margin:32px;max-width:1000px}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f5f5f5}</style></head><body>"
        "<h1>Design Debt Dashboard</h1><p>Status: <strong>" + str(report["status"]) + "</strong></p>"
        "<p>Findings: <strong>" + str(report["finding_count"]) + "</strong></p>"
        "<table><thead><tr><th>Type</th><th>Location / detail</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table></body></html>"
    )
