from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "design-intelligence" / "stage2-policy.yaml"


class DependencyIntelligenceError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DependencyIntelligenceError(f"Expected mapping in {path}")
    return value


def _days_since(date_text: str, now: datetime) -> int:
    value = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return max(0, (now - value.astimezone(timezone.utc)).days)


def evaluate_dependencies(
    snapshots: list[dict[str, Any]],
    *,
    policy: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    policy = policy or _load(POLICY)
    cfg = policy["dependencies"]
    now = now or datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []

    for source in snapshots:
        row = dict(source)
        reasons: list[str] = []
        status = "eligible"

        license_id = str(row.get("license", "unknown"))
        if license_id in cfg["license"]["block"]:
            status = "blocked"
            reasons.append("license-blocked")
        elif license_id in cfg["license"]["review"] and status != "blocked":
            status = "review"
            reasons.append("license-review")
        elif license_id not in cfg["license"]["allow"]:
            status = "review"
            reasons.append("license-unclassified")

        last_release = row.get("last_release_at")
        if not last_release:
            if status != "blocked":
                status = "review"
            reasons.append("release-date-missing")
            release_age_days = None
        else:
            release_age_days = _days_since(str(last_release), now)
            if release_age_days > int(cfg["maintenance"]["watch_max_days"]):
                status = "blocked"
                reasons.append("maintenance-stale")
            elif release_age_days > int(cfg["maintenance"]["healthy_max_days"]) and status != "blocked":
                status = "review"
                reasons.append("maintenance-watch")

        vulnerabilities = row.get("vulnerabilities", []) or []
        severities = {str(v.get("severity", "")).lower() for v in vulnerabilities if isinstance(v, dict)}
        if str(cfg["security"]["block_severity"]).lower() in severities:
            status = "blocked"
            reasons.append("critical-vulnerability")
        elif severities.intersection({str(x).lower() for x in cfg["security"]["review_severities"]}) and status != "blocked":
            status = "review"
            reasons.append("high-vulnerability")

        missing = [k for k in cfg["compatibility"]["required_fields"] if not row.get(k)]
        if missing:
            if status != "blocked":
                status = "review"
            reasons.append("compatibility-evidence-missing:" + ",".join(sorted(missing)))

        rows.append({
            **row,
            "release_age_days": release_age_days,
            "eligibility": status,
            "reasons": reasons,
        })

    overall = "blocked" if any(x["eligibility"] == "blocked" for x in rows) else (
        "review" if any(x["eligibility"] == "review" for x in rows) else "passed"
    )
    return {
        "status": overall,
        "dependencies": rows,
        "rule": cfg["rule"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic dependency-health snapshots")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = _load(args.input)
    snapshots = payload.get("dependencies", [])
    result = evaluate_dependencies(snapshots)
    rendered = yaml.safe_dump(result, sort_keys=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 2 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
