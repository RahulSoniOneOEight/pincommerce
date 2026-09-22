from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


class ImpactError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ImpactError(f"Missing impact input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ImpactError(f"Expected mapping in {path}")
    return value


def analyze_change(
    client_id: str,
    affected_capabilities: list[str],
    affected_surfaces: list[str] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    deps = _load(project / "derived" / "dependency-map.yaml")
    entities = _load(project / "derived" / "entity-map.yaml")
    integrations_path = project / "derived" / "integration-map.yaml"
    integrations = _load(integrations_path) if integrations_path.exists() else {"integrations": []}

    capability_set = set(affected_capabilities)
    domains: set[str] = set()
    flows: list[str] = []
    for flow in deps.get("critical_cross_domain_flows", []):
        flow_id = str(flow.get("id", ""))
        if any(cap.replace("_", "-") in flow_id or flow_id in cap for cap in capability_set):
            flows.append(flow_id)
            domains.update(flow.get("domains", []))

    affected_entities = [
        entity for entity, detail in entities.get("entities", {}).items()
        if detail.get("owner_capability") in capability_set
        or any(token in detail.get("owner_capability", "") for token in capability_set)
    ]

    integration_ids = [
        item["id"] for item in integrations.get("integrations", [])
        if item.get("domain") in domains or item.get("id") in capability_set
    ]

    return {
        "affected_capabilities": sorted(capability_set),
        "affected_domains": sorted(domains),
        "affected_surfaces": sorted(set(affected_surfaces or [])),
        "affected_entities": sorted(affected_entities),
        "affected_integrations": sorted(integration_ids),
        "affected_flows": sorted(flows),
        "required_tests": sorted(set(
            ["contract", "integration", "e2e"]
            + (["reconciliation"] if integrations.get("integrations") else [])
        )),
        "approval_required": bool(domains or integration_ids or affected_entities),
    }
