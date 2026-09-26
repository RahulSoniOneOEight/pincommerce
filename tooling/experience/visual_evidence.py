from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "design-intelligence" / "visual-evidence.yaml"


class VisualEvidenceError(RuntimeError):
    pass


def load_policy(path: Path = POLICY) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VisualEvidenceError("visual evidence policy must be a mapping")
    return value


def expected_captures(policy: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for pattern, story_id in sorted(policy["story_ids"].items()):
        for viewport_id, viewport in policy["viewports"].items():
            rows.append({
                "pattern": pattern,
                "story_id": story_id,
                "viewport_id": viewport_id,
                "width": int(viewport["width"]),
                "height": int(viewport["height"]),
                "file": f"{pattern}__{viewport_id}.png",
            })
    return rows


def fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def evaluate_evidence(payload: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    expected = {(r["pattern"], r["viewport_id"]) for r in expected_captures(policy)}
    captures = payload.get("captures", [])
    actual = {(str(r.get("pattern")), str(r.get("viewport_id"))) for r in captures}
    blockers: list[str] = []

    missing = sorted(expected - actual)
    if missing:
        blockers.extend(f"capture-missing:{p}:{v}" for p, v in missing)

    for row in captures:
        if not row.get("screenshot_sha256"):
            blockers.append(f"screenshot-hash-missing:{row.get('pattern')}:{row.get('viewport_id')}")
        if not row.get("dom_fingerprint"):
            blockers.append(f"dom-fingerprint-missing:{row.get('pattern')}:{row.get('viewport_id')}")
        axe = row.get("accessibility", {})
        if int(axe.get("critical", 0)) > int(policy["accessibility"]["max_critical"]):
            blockers.append(f"accessibility-critical:{row.get('pattern')}:{row.get('viewport_id')}")
        if int(axe.get("serious", 0)) > int(policy["accessibility"]["max_serious"]):
            blockers.append(f"accessibility-serious:{row.get('pattern')}:{row.get('viewport_id')}")
        if int(axe.get("unlabeled_interactive", 0)) > 0:
            blockers.append(f"accessibility-unlabeled-interactive:{row.get('pattern')}:{row.get('viewport_id')}")
        perf = row.get("performance", {})
        dcl = float(perf.get("dom_content_loaded_ms", 0))
        transfer = int(perf.get("transfer_bytes", 0))
        if dcl > float(policy["performance"]["max_dom_content_loaded_ms"]):
            blockers.append(f"performance-dcl:{row.get('pattern')}:{row.get('viewport_id')}")
        if transfer > int(policy["performance"]["max_transfer_bytes"]):
            blockers.append(f"performance-transfer:{row.get('pattern')}:{row.get('viewport_id')}")
        # End-to-end capture wall time includes Playwright/CI scheduling, screenshot
        # encoding and axe execution, so it is diagnostic only. Component performance
        # is gated by browser navigation/resource timings above.

    return {
        "status": "passed" if not blockers else "blocked",
        "capture_count": len(captures),
        "expected_count": len(expected),
        "blocking_items": blockers,
        "evidence_fingerprint": fingerprint(captures),
    }


def compare_dom_baseline(payload: dict[str, Any], baseline: dict[str, str]) -> dict[str, Any]:
    diffs = []
    for row in payload.get("captures", []):
        key = f"{row.get('pattern')}::{row.get('viewport_id')}"
        current = row.get("dom_fingerprint")
        expected = baseline.get(key)
        if expected is not None and current != expected:
            diffs.append({"key": key, "expected": expected, "actual": current})
    return {"status": "passed" if not diffs else "changed", "differences": diffs}
