from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[2]

class JourneyEngineError(RuntimeError):
    pass

SURFACE_BY_ACTOR = {
    "customer": ["customer-app", "web-store"],
    "b2b-buyer": ["b2b", "web-store"],
    "seller": ["seller-portal"],
    "operator": ["commerce-admin", "ops-console"],
    "finance": ["erp", "analytics"],
}

CAPABILITY_SURFACE = {
    "catalogue": ["customer-app", "web-store"],
    "search": ["customer-app", "web-store"],
    "cart": ["customer-app", "web-store", "b2b"],
    "checkout": ["customer-app", "web-store", "b2b"],
    "orders": ["customer-app", "web-store", "b2b", "seller-portal", "commerce-admin"],
    "fulfilment": ["customer-app", "web-store", "seller-portal", "commerce-admin"],
    "return-refund": ["customer-app", "web-store", "seller-portal", "commerce-admin"],
    "quote-rfq": ["b2b", "seller-portal", "commerce-admin"],
    "reorder": ["b2b", "web-store"],
    "credit-management": ["b2b", "commerce-admin", "erp"],
    "approval-workflow": ["b2b", "commerce-admin"],
    "seller-settlements": ["seller-portal", "commerce-admin", "erp"],
    "payout-reconciliation": ["commerce-admin", "erp", "analytics"],
}

DEFAULT_JOURNEYS = {
    "browse-to-buy": [
        ("discover", "catalogue"), ("select-product", "catalogue"), ("add-cart", "cart"),
        ("checkout", "checkout"), ("payment", "checkout"), ("confirm-order", "orders"),
    ],
    "search-to-buy": [
        ("search", "search"), ("select-product", "catalogue"), ("add-cart", "cart"),
        ("checkout", "checkout"), ("confirm-order", "orders"),
    ],
    "order-tracking": [("open-order", "orders"), ("track-shipment", "fulfilment")],
    "return-refund": [
        ("open-order", "orders"), ("request-return", "return-refund"),
        ("seller-review", "return-refund"), ("track-refund", "return-refund"),
    ],
    "quote-to-order": [
        ("create-rfq", "quote-rfq"), ("seller-quote", "quote-rfq"),
        ("buyer-accept", "quote-rfq"), ("checkout", "checkout"), ("confirm-order", "orders"),
    ],
    "repeat-order": [("order-history", "orders"), ("reorder", "reorder"), ("checkout", "checkout")],
    "credit-order": [
        ("choose-credit", "credit-management"), ("approval", "approval-workflow"),
        ("checkout", "checkout"), ("confirm-order", "orders"),
    ],
    "seller-settlement": [
        ("review-orders", "orders"), ("calculate-settlement", "seller-settlements"),
        ("post-accounting", "seller-settlements"), ("reconcile-payout", "payout-reconciliation"),
    ],
}

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise JourneyEngineError(f"Missing journey input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise JourneyEngineError(f"Expected mapping: {path}")
    return value

def _actor(journey_id: str) -> str:
    if "seller" in journey_id:
        return "seller"
    if any(x in journey_id for x in ("quote", "credit", "repeat")):
        return "b2b-buyer"
    if "reconciliation" in journey_id:
        return "finance"
    return "customer"

def _surface(capability: str, actor: str, required: list[str], previous: str | None = None) -> str:
    candidates = CAPABILITY_SURFACE.get(capability, []) + SURFACE_BY_ACTOR.get(actor, [])
    if previous and previous in candidates and previous in required:
        return previous
    for candidate in candidates:
        if candidate in required:
            return candidate
    if required:
        return required[0]
    raise JourneyEngineError("No required surfaces are defined")

def build(client_id: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    journey_map = _load(project / "derived" / "journey-map.yaml")
    surface_map = _load(project / "derived" / "surface-map.yaml")
    required = list(surface_map.get("required", []))
    journeys = []
    for spec in journey_map.get("journeys", []):
        journey_id = str(spec["id"])
        actor = str(spec.get("actor") or _actor(journey_id))
        raw_steps = spec.get("steps") or DEFAULT_JOURNEYS.get(journey_id)
        if not raw_steps:
            raw_steps = [(journey_id, str(spec.get("capability") or "orders"))]
        steps = []
        for item in raw_steps:
            if isinstance(item, dict):
                steps.append((str(item["action"]), str(item.get("capability") or "orders")))
            else:
                steps.append((str(item[0]), str(item[1])))
        nodes = []
        previous_surface = None
        used_surfaces = []
        for index, (action, capability) in enumerate(steps, 1):
            surface = _surface(capability, actor, required, previous_surface)
            handoff = previous_surface is not None and surface != previous_surface
            node_id = f"{journey_id}.{index}"
            success_next = [f"{journey_id}.{index + 1}"] if index < len(steps) else []
            node = {
                "id": node_id,
                "actor": actor,
                "action": action,
                "surface": surface,
                "screen": action.replace("-", "_"),
                "capability": capability,
                "data": [f"{capability}.read", f"{capability}.write"],
                "permission": actor,
                "backend_operation": f"{capability}.{action}",
                "event": f"{journey_id}.{action}.completed",
                "success_state": f"{action}-success",
                "error_state": f"{action}-error",
                "empty_state": f"{action}-empty",
                "loading_state": f"{action}-loading",
                "next": success_next,
                "branches": [
                    {"when": "success", "next": success_next},
                    {"when": "error", "state": f"{action}-error", "recover": node_id},
                ],
                "handoff": {
                    "required": handoff,
                    "from": previous_surface if handoff else None,
                    "to": surface if handoff else None,
                },
            }
            nodes.append(node)
            used_surfaces.append(surface)
            previous_surface = surface
        journeys.append({
            "id": journey_id,
            "actor": actor,
            "objective": spec.get("objective") or journey_id.replace("-", " "),
            "surfaces": list(dict.fromkeys(used_surfaces)),
            "nodes": nodes,
            "completion": nodes[-1]["success_state"],
        })
    if not journeys:
        raise JourneyEngineError("No journeys found")
    return {"client_id": client_id, "journeys": journeys, "status": "generated"}

def validate_executable(graph: dict[str, Any]) -> list[str]:
    errors = []
    for journey in graph.get("journeys", []):
        ids = {node.get("id") for node in journey.get("nodes", [])}
        if not ids:
            errors.append(f"{journey.get('id')}: no nodes")
            continue
        for node in journey.get("nodes", []):
            for field in ("actor","action","surface","screen","capability","permission","backend_operation","success_state","error_state","loading_state","branches"):
                if not node.get(field):
                    errors.append(f"{node.get('id')}: missing {field}")
            for target in node.get("next", []):
                if target not in ids:
                    errors.append(f"{node.get('id')}: invalid next {target}")
    return errors
