from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

API_ROOT = "https://api.pexels.com/v1"


class PexelsAssetError(RuntimeError):
    pass


def search_photos(
    query: str,
    *,
    orientation: str | None = None,
    per_page: int = 8,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    key = api_key or os.getenv("PEXELS_API_KEY", "")
    if not key:
        raise PexelsAssetError("PEXELS_API_KEY is required")
    params = {"query": query, "per_page": max(1, min(per_page, 10))}
    if orientation:
        params["orientation"] = orientation
    url = API_ROOT + "/search?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Authorization": key})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    candidates = []
    for photo in payload.get("photos", []):
        candidates.append({
            "provider": "pexels",
            "provider_asset_id": str(photo.get("id")),
            "source_page_url": photo.get("url"),
            "photographer": photo.get("photographer"),
            "photographer_url": photo.get("photographer_url"),
            "width": photo.get("width"),
            "height": photo.get("height"),
            "alt": photo.get("alt"),
            "src": photo.get("src", {}),
        })
    return candidates


def resolve_asset_plan(plan_path: Path, output_path: Path) -> dict[str, Any]:
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        raise PexelsAssetError("asset plan must be a mapping")
    for request in plan.get("requests", []):
        if request.get("selected_asset"):
            continue
        policy = request.get("provider_policy", "")
        if "pexels-if-missing" not in policy:
            continue
        query = request.get("query", {})
        candidates = search_photos(
            str(query.get("text", "commerce")),
            orientation=query.get("orientation"),
            per_page=int(query.get("candidate_count", 8)),
        )
        request["pexels_candidates"] = candidates
        request["status"] = "planned" if candidates else "blocked"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve missing design imagery through Pexels")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = resolve_asset_plan(args.plan, args.output)
        print(yaml.safe_dump(result, sort_keys=False))
        return 0
    except PexelsAssetError as exc:
        print(f"pexels-asset-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
