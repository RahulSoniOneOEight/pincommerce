from __future__ import annotations

import json
import os
import re
import urllib.request
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urljoin

from tooling.experience.source_ingestion import ingest


class ConnectorError(RuntimeError):
    pass


def _json_get(url: str, headers: dict[str, str] | None = None, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {})
    with opener(request, timeout=30) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ConnectorError(f"Expected JSON object from {url}")
    return value


def _flatten_figma_nodes(node: dict[str, Any], out: list[dict[str, Any]], depth: int = 0) -> None:
    if depth > 8:
        return
    node_type = str(node.get("type") or "")
    if node_type in {"CANVAS","FRAME","COMPONENT","COMPONENT_SET","INSTANCE"}:
        out.append({
            "id": node.get("id"),
            "name": node.get("name"),
            "type": node_type,
            "layout_mode": node.get("layoutMode"),
            "item_spacing": node.get("itemSpacing"),
            "padding": {
                "top": node.get("paddingTop"), "right": node.get("paddingRight"),
                "bottom": node.get("paddingBottom"), "left": node.get("paddingLeft"),
            },
        })
    for child in node.get("children", []) or []:
        if isinstance(child, dict):
            _flatten_figma_nodes(child, out, depth + 1)


def fetch_figma(file_key: str, *, token: str | None = None, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    token = token or os.getenv("FIGMA_TOKEN")
    if not token:
        raise ConnectorError("FIGMA_TOKEN is required")
    payload = _json_get(f"https://api.figma.com/v1/files/{file_key}", {"X-Figma-Token": token}, opener)
    hierarchy: list[dict[str, Any]] = []
    if isinstance(payload.get("document"), dict):
        _flatten_figma_nodes(payload["document"], hierarchy)
    normalized = {
        "file_key": file_key,
        "components": [{"id": k, **v} for k, v in payload.get("components", {}).items()] if isinstance(payload.get("components"), dict) else [],
        "componentSets": [{"id": k, **v} for k, v in payload.get("componentSets", {}).items()] if isinstance(payload.get("componentSets"), dict) else [],
        "variables": payload.get("variables", {}),
        "patterns": [{"id": x.get("id"), "name": x.get("name"), "kind": x.get("type"), "evidence": x} for x in hierarchy],
        "notes": [f"name:{payload.get('name', '')}", f"hierarchy_nodes:{len(hierarchy)}"],
    }
    return ingest("figma", f"figma:{file_key}", normalized)


def fetch_penpot(project_id: str, *, api_url: str | None = None, token: str | None = None, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    api_url = api_url or os.getenv("PENPOT_API_URL")
    token = token or os.getenv("PENPOT_TOKEN")
    if not api_url or not token:
        raise ConnectorError("PENPOT_API_URL and PENPOT_TOKEN are required")
    url = api_url.rstrip("/") + f"/projects/{project_id}/design-export"
    payload = _json_get(url, {"Authorization": f"Bearer {token}"}, opener)
    payload = {"project_id": project_id, **payload}
    return ingest("penpot", f"penpot:{project_id}", payload)


def fetch_github_reference(owner: str, repo: str, *, token: str | None = None, ref: str = "HEAD", opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "PinCommerce-DesignIntelligence/1.0"}
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    meta = _json_get(f"https://api.github.com/repos/{owner}/{repo}", headers, opener)
    tree = _json_get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1", headers, opener)
    paths = [str(x.get("path")) for x in tree.get("tree", []) if isinstance(x, dict) and x.get("type") == "blob"]
    ui_paths = [x for x in paths if re.search(r"(component|widget|screen|page|layout|theme|token|style|icon)", x, re.I)]
    payload = {
        "source_ref": meta.get("html_url"),
        "components": [{"name": p.split("/")[-1], "id": p, "type": "repository-file"} for p in ui_paths[:500]],
        "patterns": [{"id": f"path-{i+1}", "name": p, "kind": "ui-file", "evidence": p} for i, p in enumerate(ui_paths[:500])],
        "notes": [f"default_branch:{meta.get('default_branch')}", f"language:{meta.get('language')}", f"files:{len(paths)}"],
    }
    return ingest("git", f"github:{owner}/{repo}", payload)


class _ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stylesheets: list[str] = []
        self.meta: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.links: list[str] = []
        self.headings: list[str] = []
        self.controls: list[str] = []
        self._capture_heading: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k: v or "" for k, v in attrs}
        if tag == "link" and "stylesheet" in values.get("rel", "") and values.get("href"):
            self.stylesheets.append(values["href"])
        if tag == "meta" and (values.get("name") or values.get("property")):
            self.meta.append({"key": values.get("name") or values.get("property", ""), "content": values.get("content", "")})
        if tag == "img" and values.get("src"):
            self.images.append({"src": values["src"], "alt": values.get("alt", "")})
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag in {"button","input","select","textarea","nav","header","aside"}:
            self.controls.append(tag + ":" + (values.get("aria-label") or values.get("role") or values.get("class") or ""))
        if tag in {"h1","h2","h3"}:
            self._capture_heading = tag
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._capture_heading:
            self._text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if self._capture_heading == tag:
            value = " ".join(x for x in self._text if x).strip()
            if value:
                self.headings.append(value)
            self._capture_heading = None
            self._text = []


def extract_reference_site(url: str, *, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "PinCommerce-DesignIntelligence/1.0"})
    with opener(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = _ReferenceParser()
    parser.feed(html)
    colors = sorted(set(re.findall(r"#[0-9A-Fa-f]{6}\b", html)))
    payload = {
        "source_ref": url,
        "colors": {f"color_{i+1}": value for i, value in enumerate(colors[:50])},
        "patterns": [
            *[{"id": f"heading-{i+1}", "name": value, "kind": "content-hierarchy", "evidence": value} for i, value in enumerate(parser.headings[:100])],
            *[{"id": f"control-{i+1}", "name": value, "kind": "interaction-control", "evidence": value} for i, value in enumerate(parser.controls[:100])],
        ],
        "assets": [
            *[{"type": "stylesheet", "ref": urljoin(url, href)} for href in parser.stylesheets],
            *[{"type": "image", "ref": urljoin(url, img["src"]), "alt": img["alt"]} for img in parser.images[:100]],
        ],
        "notes": [
            *[f"meta:{m['key']}={m['content']}" for m in parser.meta[:50]],
            *[f"link:{urljoin(url, x)}" for x in parser.links[:100]],
        ],
    }
    return ingest("reference-site", url, payload)
