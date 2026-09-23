from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

PROVIDERS = {
    "razorpay": ("RAZORPAY_STAGING_URL", "RAZORPAY_STAGING_AUTH"),
    "shiprocket": ("SHIPROCKET_STAGING_URL", "SHIPROCKET_STAGING_AUTH"),
    "meta-whatsapp-cloud": ("WHATSAPP_STAGING_URL", "WHATSAPP_STAGING_AUTH"),
}


def probe(url: str, auth: str, timeout: int = 15) -> tuple[str, str]:
    request = urllib.request.Request(url, method="GET")
    if auth:
        request.add_header("Authorization", auth)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            code = int(response.status)
            body = response.read(512).decode("utf-8", errors="replace")
            if 200 <= code < 400:
                return "pass", f"HTTP {code}: {body[:160]}"
            return "fail", f"HTTP {code}: {body[:160]}"
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return "fail", str(exc)


def collect(candidate_id: str) -> dict[str, Any]:
    rows = []
    for provider, (url_env, auth_env) in PROVIDERS.items():
        url = os.getenv(url_env, "").strip()
        auth = os.getenv(auth_env, "").strip()
        if not url:
            rows.append({
                "id": provider,
                "mode": "sandbox",
                "credential_ref": f"env:{auth_env}",
                "status": "not-run",
                "evidence": f"missing {url_env}",
            })
            continue
        status, evidence = probe(url, auth)
        rows.append({
            "id": provider,
            "mode": "sandbox" if provider != "meta-whatsapp-cloud" else "staging",
            "credential_ref": f"env:{auth_env}",
            "status": status,
            "evidence": evidence,
        })
    if any(row["status"] == "fail" for row in rows):
        overall = "failed"
    elif any(row["status"] == "not-run" for row in rows):
        overall = "blocked"
    else:
        overall = "passed"
    return {
        "evidence_id": f"PROVSTG-{candidate_id}",
        "candidate_id": candidate_id,
        "providers": rows,
        "status": overall,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect live provider staging probes")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.candidate_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
