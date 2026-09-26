from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SUPPORTED = {"figma", "penpot", "git", "reference-site", "brand-guide", "client-media"}


class SourceIngestionError(RuntimeError):
    pass


def _hash(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def ingest(source_type: str, source_id: str, payload: dict[str, Any], *, captured_at: str | None = None) -> dict[str, Any]:
    if source_type not in SUPPORTED:
        raise SourceIngestionError(f"Unsupported source type: {source_type}")
    captured_at = captured_at or datetime.now(timezone.utc).isoformat()
    if source_type == "figma":
        normalized = {
            "source_ref": payload.get("file_key") or payload.get("source_ref"),
            "components": _list(payload.get("components")) or _list(payload.get("componentSets")),
            "tokens": _mapping(payload.get("variables")) or _mapping(payload.get("tokens")),
            "patterns": _list(payload.get("patterns")),
            "assets": _list(payload.get("assets")),
            "notes": _list(payload.get("notes")),
        }
    elif source_type == "penpot":
        normalized = {
            "source_ref": payload.get("project_id") or payload.get("source_ref"),
            "components": _list(payload.get("components")),
            "tokens": _mapping(payload.get("tokens")),
            "colors": _mapping(payload.get("colors")),
            "typography": _mapping(payload.get("typography")),
            "spacing": _mapping(payload.get("spacing")),
            "radii": _mapping(payload.get("radii")),
            "patterns": _list(payload.get("patterns")),
            "assets": _list(payload.get("assets")),
            "notes": _list(payload.get("notes")),
        }
    else:
        normalized = {
            "source_ref": payload.get("source_ref"),
            "components": _list(payload.get("components")),
            "tokens": _mapping(payload.get("tokens")),
            "colors": _mapping(payload.get("colors")),
            "typography": _mapping(payload.get("typography")),
            "spacing": _mapping(payload.get("spacing")),
            "radii": _mapping(payload.get("radii")),
            "patterns": _list(payload.get("patterns")),
            "assets": _list(payload.get("assets")),
            "notes": _list(payload.get("notes")),
        }
    return {
        "source_id": source_id,
        "type": source_type,
        "provenance": {
            "source_id": source_id,
            "source_type": source_type,
            "captured_at": captured_at,
            "content_hash": _hash(payload),
            "source_ref": normalized.get("source_ref"),
        },
        **normalized,
        "status": "normalized",
    }


def merge_inventory(records: list[dict[str, Any]]) -> dict[str, Any]:
    seen: set[tuple[str, str]] = set()
    sources: list[dict[str, Any]] = []
    for record in records:
        key = (str(record.get("type")), str(record.get("source_id")))
        if key in seen:
            raise SourceIngestionError(f"Duplicate source: {key[0]}:{key[1]}")
        seen.add(key)
        if record.get("status") != "normalized" or not record.get("provenance", {}).get("content_hash"):
            raise SourceIngestionError(f"Unprovenanced source: {key[0]}:{key[1]}")
        sources.append(record)
    return {"version": 1, "sources": sources, "source_count": len(sources), "status": "ready"}
