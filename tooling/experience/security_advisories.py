from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable


def collect_osv(package: str, ecosystem: str, version: str, *, opener: Callable[..., Any] = urllib.request.urlopen) -> list[dict[str, Any]]:
    payload = json.dumps({"package": {"name": package, "ecosystem": ecosystem}, "version": version}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.osv.dev/v1/query",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "PinCommerce-DependencyCollector/1.0"},
        method="POST",
    )
    with opener(request, timeout=30) as response:
        value = json.loads(response.read().decode("utf-8"))
    result = []
    for vuln in value.get("vulns", []):
        severity_rows = vuln.get("severity", [])
        score_text = " ".join(str(s.get("score", "")) for s in severity_rows if isinstance(s, dict))
        severity = "critical" if "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H" in score_text else "review"
        result.append({
            "id": vuln.get("id"),
            "severity": severity,
            "summary": vuln.get("summary"),
            "aliases": vuln.get("aliases", []),
        })
    return result
