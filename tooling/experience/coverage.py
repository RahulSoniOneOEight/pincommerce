from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_STATES = ["default", "loading", "empty", "failure"]

CAPABILITY_UX = {
    "catalogue": {
        "screens": ["home", "category", "product-list", "product-detail"],
        "components": ["category-navigation", "product-card", "product-gallery", "variant-selector"],
        "states": ["default", "loading", "empty", "failure", "out-of-stock"],
    },
    "search": {
        "screens": ["search", "search-results"],
        "components": ["search-bar", "search-suggestions", "filter-control", "sort-control"],
        "states": ["default", "loading", "empty", "failure", "no-results"],
    },
    "promotions": {
        "screens": ["home", "cart", "checkout"],
        "components": ["promotion-banner", "coupon-entry", "discount-breakdown"],
        "states": ["default", "coupon-valid", "coupon-invalid"],
    },
    "cart": {
        "screens": ["cart"],
        "components": ["cart-line", "quantity-selector", "price-summary"],
        "states": ["default", "empty", "out-of-stock"],
    },
    "checkout": {
        "screens": ["checkout", "address", "delivery", "payment", "order-confirmation"],
        "components": ["address-card", "delivery-option", "payment-method", "order-summary"],
        "states": ["default", "loading", "failure", "payment-failed", "order-success"],
    },
    "orders": {
        "screens": ["orders", "order-detail"],
        "components": ["order-card", "order-status", "order-timeline"],
        "states": ["default", "empty", "loading", "failure"],
    },
    "return-refund": {
        "screens": ["return-request", "return-status"],
        "components": ["return-reason", "pickup-option", "refund-status"],
        "states": ["default", "approval-pending", "rejected", "refunded"],
    },
    "inventory-availability": {
        "screens": ["product-detail", "inventory"],
        "components": ["availability-indicator", "warehouse-availability"],
        "states": ["in-stock", "low-stock", "out-of-stock"],
    },
    "credit-management": {
        "screens": ["account", "checkout"],
        "components": ["credit-limit-card", "credit-balance", "credit-status"],
        "states": ["available", "partially-used", "limit-exceeded", "approval-pending"],
    },
    "approval-workflow": {
        "screens": ["checkout", "approval-status"],
        "components": ["approval-banner", "approver-status", "approval-action"],
        "states": ["approval-pending", "approved", "rejected"],
    },
    "quote-rfq": {
        "screens": ["rfq", "quote-detail"],
        "components": ["rfq-form", "quote-line", "quote-status"],
        "states": ["draft", "submitted", "approved", "rejected"],
    },
    "customer-support": {
        "screens": ["support"],
        "components": ["support-entry", "whatsapp-cta", "ticket-status"],
        "states": ["default", "loading", "failure"],
    },
    "analytics": {
        "screens": ["dashboard"],
        "components": ["metric-card", "trend-chart", "filter-bar"],
        "states": ["default", "loading", "empty", "failure"],
    },
    "ops-exceptions": {
        "screens": ["exceptions", "exception-detail"],
        "components": ["exception-card", "retry-action", "replay-action", "status-chip"],
        "states": ["open", "retrying", "resolved", "failed"],
    },
}

SURFACE_DEFAULTS = {
    "customer-app": {
        "screens": ["home", "search", "product-list", "product-detail", "cart", "checkout", "orders", "profile"],
        "components": ["navigation", "search-bar", "product-card", "cart-line", "order-card"],
    },
    "web-store": {
        "screens": ["home", "search", "product-list", "product-detail", "cart", "checkout", "account", "orders"],
        "components": ["header", "navigation", "search-bar", "product-card", "cart-line", "order-card"],
    },
    "commerce-admin": {
        "screens": ["dashboard", "products", "orders", "inventory", "promotions", "returns", "customers", "settings"],
        "components": ["data-table", "filter-bar", "form", "status-chip", "bulk-actions"],
    },
    "seller-portal": {
        "screens": ["dashboard", "catalogue", "inventory", "pricing", "orders", "returns", "settlements", "settings"],
        "components": ["metric-card", "data-table", "filter-bar", "form", "status-chip"],
    },
    "ops-console": {
        "screens": ["exceptions", "payments", "shipments", "reconciliation", "health"],
        "components": ["exception-card", "data-table", "retry-action", "replay-action", "status-chip"],
    },
    "analytics": {
        "screens": ["dashboard", "sales", "orders", "inventory", "fulfilment", "customers"],
        "components": ["metric-card", "trend-chart", "filter-bar", "data-table"],
    },
    "erp": {
        "screens": ["products", "sales-orders", "purchases", "inventory", "warehouse", "invoices"],
        "components": ["data-table", "form", "status-chip", "document-lines"],
    },
    "warehouse": {
        "screens": ["stock", "transfers", "picking", "receiving"],
        "components": ["data-table", "scanner-input", "transfer-status"],
    },
    "customer-support": {
        "screens": ["conversations", "customer-context"],
        "components": ["conversation-list", "message-thread", "customer-card"],
    },
}


class CoverageError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CoverageError(f"Missing prototype coverage input: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CoverageError(f"Expected mapping in {path}")
    return value


def _uniq(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def _requirements(client_input: dict[str, Any]) -> list[dict[str, Any]]:
    explicit = client_input.get("experience_requirements", [])
    requirements: list[dict[str, Any]] = []
    for idx, item in enumerate(explicit, start=1):
        if isinstance(item, str):
            requirements.append({
                "requirement_id": f"REQ-CLIENT-{idx:03d}",
                "statement": item,
                "ux_impact": True,
                "source_refs": list(client_input.get("source_refs", [])),
                "requested_surfaces": [],
                "requested_screens": [],
                "requested_components": [],
                "required_states": [],
                "decision": None,
                "decision_reason": None,
            })
        elif isinstance(item, dict):
            requirements.append({
                "requirement_id": item.get("requirement_id", f"REQ-CLIENT-{idx:03d}"),
                "statement": item["statement"],
                "ux_impact": item.get("ux_impact", True),
                "source_refs": item.get("source_refs", client_input.get("source_refs", [])),
                "requested_surfaces": item.get("requested_surfaces", []),
                "requested_screens": item.get("requested_screens", []),
                "requested_components": item.get("requested_components", []),
                "required_states": item.get("required_states", []),
                "decision": item.get("decision"),
                "decision_reason": item.get("decision_reason"),
            })
    return requirements


def build_coverage(
    client_id: str,
    direction_file: str = "a.yaml",
    root: Path = ROOT,
    require_implementation: bool = True,
) -> dict[str, Any]:
    project = root / "client-projects" / client_id
    client_input = load_yaml(project / "input" / "client-input.yaml")
    capability_map = load_yaml(project / "derived" / "capability-map.yaml")
    journey_map = load_yaml(project / "derived" / "journey-map.yaml")
    surface_map = load_yaml(project / "derived" / "surface-map.yaml")
    direction = load_yaml(project / "experience" / "directions" / direction_file)
    manifest_name = direction_file.replace(".yaml", "-manifest.yaml")
    manifest = load_yaml(project / "experience" / "prototypes" / manifest_name)
    suffix = direction_file.replace(".yaml", "")
    implementation_path = project / "experience" / "prototypes" / f"{suffix}-implementation.yaml"
    implementation = None
    implementation_ref = None
    if implementation_path.exists():
        implementation = load_yaml(implementation_path)
        errors = validate_document(implementation, "prototype-implementation")
        if errors:
            raise CoverageError("Invalid prototype implementation evidence: " + "; ".join(errors))
        implementation_ref = f"experience/prototypes/{implementation_path.name}"

    required_surfaces = list(surface_map.get("required", []))
    journeys = [
        item.get("id") if isinstance(item, dict) else item
        for item in journey_map.get("journeys", [])
    ]
    capabilities = _uniq(
        list(capability_map.get("mandatory", []))
        + list(capability_map.get("core", []))
        + list(capability_map.get("recommended", []))
        + list(capability_map.get("requested_additional", []))
    )

    req_records: list[dict[str, Any]] = []
    blocking: list[str] = []
    for req in _requirements(client_input):
        if req.get("decision") in {"deferred", "not-applicable"}:
            req_records.append({
                "requirement_id": req["requirement_id"],
                "statement": req["statement"],
                "ux_impact": bool(req["ux_impact"]),
                "source_refs": list(req["source_refs"]),
                "prototype_coverage": [],
                "decision_reason": req.get("decision_reason"),
                "status": req["decision"],
            })
            continue

        coverage = []
        surfaces = req["requested_surfaces"]
        if req["ux_impact"] and not surfaces:
            surfaces = list(required_surfaces)

        has_explicit_ui = bool(
            req["requested_screens"] or req["requested_components"] or req["required_states"]
        )
        if req["ux_impact"] and surfaces and has_explicit_ui:
            for surface in surfaces:
                coverage.append({
                    "surface": surface,
                    "screens": list(req["requested_screens"]),
                    "components": list(req["requested_components"]),
                    "states": list(req["required_states"] or DEFAULT_STATES),
                })
            status = "covered"
        elif not req["ux_impact"]:
            status = "not-applicable"
        else:
            status = "unmapped"
            blocking.append(
                f"{req['requirement_id']}: UX-impacting client requirement has no screen/component/state mapping"
            )

        req_records.append({
            "requirement_id": req["requirement_id"],
            "statement": req["statement"],
            "ux_impact": bool(req["ux_impact"]),
            "source_refs": list(req["source_refs"]),
            "prototype_coverage": coverage,
            "decision_reason": req.get("decision_reason"),
            "status": status,
        })

    implementation_by_surface = {
        item["surface"]: item
        for item in (implementation or {}).get("surfaces", [])
    }

    surface_records = []
    if require_implementation and implementation is None:
        blocking.append(
            f"prototype implementation evidence missing: experience/prototypes/{suffix}-implementation.yaml"
        )

    for surface in required_surfaces:
        defaults = SURFACE_DEFAULTS.get(surface, {"screens": [], "components": []})
        screens = list(defaults["screens"])
        components = list(defaults["components"])
        states = list(DEFAULT_STATES)

        for capability in capabilities:
            ux = CAPABILITY_UX.get(capability)
            if ux:
                screens.extend(ux["screens"])
                components.extend(ux["components"])
                states.extend(ux["states"])

        for req in req_records:
            for coverage in req["prototype_coverage"]:
                if coverage["surface"] == surface:
                    screens.extend(coverage["screens"])
                    components.extend(coverage["components"])
                    states.extend(coverage["states"])

        screens = _uniq(screens)
        components = _uniq(components)
        states = _uniq(states)
        complete = bool(screens and components and states and journeys)
        if not complete:
            blocking.append(f"surface:{surface}: missing screen/component/state/journey coverage")

        if require_implementation and implementation is not None:
            evidence = implementation_by_surface.get(surface)
            if evidence is None:
                complete = False
                blocking.append(f"surface:{surface}: implementation evidence missing")
            else:
                implemented_screens = {
                    item["id"] for item in evidence.get("screens", [])
                    if item.get("status") == "implemented" and item.get("evidence_ref")
                }
                implemented_components = {
                    item["id"] for item in evidence.get("components", [])
                    if item.get("status") == "implemented" and item.get("evidence_ref")
                }
                implemented_states = {
                    item["id"] for item in evidence.get("states", [])
                    if item.get("status") == "implemented" and item.get("evidence_ref")
                }
                missing_screens = [item for item in screens if item not in implemented_screens]
                missing_components = [item for item in components if item not in implemented_components]
                missing_states = [item for item in states if item not in implemented_states]
                if missing_screens:
                    complete = False
                    blocking.append(
                        f"surface:{surface}: unimplemented screens: " + ", ".join(missing_screens)
                    )
                if missing_components:
                    complete = False
                    blocking.append(
                        f"surface:{surface}: unimplemented components: " + ", ".join(missing_components)
                    )
                if missing_states:
                    complete = False
                    blocking.append(
                        f"surface:{surface}: unimplemented states: " + ", ".join(missing_states)
                    )
                if evidence.get("status") != "complete":
                    complete = False
                    blocking.append(f"surface:{surface}: implementation status is not complete")

        surface_records.append({
            "surface": surface,
            "required": True,
            "screens": screens,
            "components": components,
            "states": states,
            "journeys": _uniq(journeys),
            "status": "complete" if complete else "incomplete",
        })

    status = "client-review-ready" if not blocking else "incomplete"
    result = {
        "coverage_id": f"COV-{client_id}-{direction['direction_id'].split('-')[-1].lower()}",
        "client_id": client_id,
        "direction_id": direction["direction_id"],
        "prototype_manifest_ref": f"experience/prototypes/{manifest_name}",
        "implementation_ref": implementation_ref,
        "requirements": req_records,
        "surface_coverage": surface_records,
        "blocking_items": blocking,
        "status": status,
    }
    errors = validate_document(result, "prototype-coverage")
    if errors:
        raise CoverageError("Generated prototype coverage invalid: " + "; ".join(errors))
    return result


def write_coverage(client_id: str, direction_file: str = "a.yaml", root: Path = ROOT) -> Path:
    result = build_coverage(client_id, direction_file, root)
    suffix = direction_file.replace(".yaml", "")
    path = root / "client-projects" / client_id / "experience" / "prototypes" / f"{suffix}-coverage.yaml"
    path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    return path


def assert_client_review_ready(client_id: str, direction_file: str = "a.yaml", root: Path = ROOT) -> dict[str, Any]:
    result = build_coverage(client_id, direction_file, root)
    if result["status"] != "client-review-ready":
        raise CoverageError(
            "Prototype is not client-review-ready: " + "; ".join(result["blocking_items"])
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and enforce brief-to-prototype coverage")
    parser.add_argument("--client", required=True)
    parser.add_argument("--direction", default="a.yaml")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = build_coverage(args.client, args.direction, args.root)
        if args.check:
            if result["status"] != "client-review-ready":
                print("prototype-coverage-error: " + "; ".join(result["blocking_items"]))
                return 2
            print("Prototype coverage is client-review-ready.")
            return 0
        path = write_coverage(args.client, args.direction, args.root)
        print(path.relative_to(args.root))
        return 0
    except CoverageError as exc:
        print(f"prototype-coverage-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
