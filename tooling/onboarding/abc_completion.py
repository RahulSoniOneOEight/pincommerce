from __future__ import annotations

from typing import Any

PROVIDER_CANDIDATES = {
    "payment": ["razorpay", "cashfree"],
    "payments": ["razorpay", "cashfree"],
    "logistics": ["shiprocket", "delhivery"],
    "shipping": ["shiprocket", "delhivery"],
    "whatsapp": ["meta-whatsapp-cloud"],
    "messaging": ["meta-whatsapp-cloud"],
    "commerce": ["medusa"],
    "erp": ["tryton"],
    "search": ["meilisearch"],
    "automation": ["activepieces", "n8n"],
    "support": ["chatwoot"],
}

DOMAIN_BY_INTEGRATION = {
    "payment": "payments",
    "payments": "payments",
    "logistics": "logistics",
    "shipping": "logistics",
    "whatsapp": "messaging",
    "messaging": "messaging",
    "commerce": "commerce",
    "erp": "erp",
    "search": "search",
    "automation": "automation",
    "support": "customer-support",
}

CRITICALITY = {
    "payment": "critical",
    "payments": "critical",
    "logistics": "high",
    "shipping": "high",
    "erp": "critical",
    "commerce": "critical",
    "whatsapp": "medium",
    "messaging": "medium",
    "search": "medium",
    "automation": "medium",
    "support": "medium",
}


def build_truth_register(client_input: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    sources = list(client_input.get("source_refs", [])) or ["input/client-input.yaml"]

    fact_fields = (
        "industry", "business_models", "goals", "requested_capabilities",
        "required_integrations", "existing_systems", "channels", "volumes",
        "stakeholders", "compliance", "constraints", "geographies", "risk_profile",
        "experience_requirements",
    )
    seq = 1
    for field in fact_fields:
        value = client_input.get(field)
        if value in (None, [], {}, ""):
            continue
        records.append({
            "truth_id": f"TRUTH-{seq:04d}",
            "path": field,
            "value": value,
            "classification": "fact",
            "confidence": 1.0,
            "sources": sources,
            "status": "confirmed",
            "notes": [],
        })
        seq += 1

    for assumption in client_input.get("assumptions", []):
        records.append({
            "truth_id": f"TRUTH-{seq:04d}",
            "path": "assumptions",
            "value": assumption,
            "classification": "assumption",
            "confidence": 0.5,
            "sources": sources,
            "status": "open",
            "notes": ["Requires explicit confirmation before production scope freeze."],
        })
        seq += 1

    questions = list(client_input.get("open_questions", []))
    conflicts = list(client_input.get("conflicts", []))
    for question in questions:
        records.append({
            "truth_id": f"TRUTH-{seq:04d}",
            "path": "open_questions",
            "value": question,
            "classification": "unknown",
            "confidence": 0.0,
            "sources": sources,
            "status": "open",
            "notes": [],
        })
        seq += 1

    for conflict in conflicts:
        records.append({
            "truth_id": f"TRUTH-{seq:04d}",
            "path": "conflicts",
            "value": conflict,
            "classification": "conflict",
            "confidence": 0.0,
            "sources": sources,
            "status": "open",
            "notes": ["Resolve contradiction before scope freeze."],
        })
        seq += 1

    return {
        "client_id": client_input["client_id"],
        "version": int(client_input.get("version", 1)),
        "records": records,
        "open_questions": questions,
        "conflicts": conflicts,
        "status": "needs-input" if questions or conflicts else "review-ready",
    }


def classification_evidence(
    business_models: list[str], archetype_ids: list[str], override: dict[str, Any] | None = None
) -> dict[str, Any]:
    evidence = [
        {"business_model": model, "rule": "business-model-to-archetype"}
        for model in business_models
    ]
    result = {
        "archetypes": archetype_ids,
        "confidence": 1.0 if archetype_ids else 0.0,
        "method": "deterministic-rules",
        "evidence": evidence,
        "human_override": None,
    }
    if override:
        result["archetypes"] = list(override.get("archetypes", archetype_ids))
        result["confidence"] = 1.0
        result["method"] = "human-override"
        result["human_override"] = override
    return result


def enrich_capability_gap(gap: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for capability in gap.get("core_missing", []):
        items.append({
            "capability": capability,
            "gap_type": "core-missing",
            "severity": "high",
            "priority": 1,
            "impact": ["critical-journey", "scope"],
            "recommendation": "include-or-explicitly-exclude",
        })
    for capability in gap.get("recommended_missing", []):
        items.append({
            "capability": capability,
            "gap_type": "recommended-missing",
            "severity": "medium",
            "priority": 2,
            "impact": ["best-practice"],
            "recommendation": "evaluate",
        })
    for capability in gap.get("not_in_reference_baseline", []):
        items.append({
            "capability": capability,
            "gap_type": "client-specific",
            "severity": "review",
            "priority": 2,
            "impact": ["custom-scope", "architecture-review"],
            "recommendation": "reuse-extend-build-analysis",
        })
    enriched = dict(gap)
    enriched["items"] = items
    enriched["blocking_count"] = sum(1 for item in items if item["severity"] == "high")
    return enriched


def build_integration_map(client_input: dict[str, Any]) -> dict[str, Any]:
    integrations = []
    for raw in client_input.get("required_integrations", []):
        key = str(raw).lower()
        integrations.append({
            "id": key,
            "domain": DOMAIN_BY_INTEGRATION.get(key, key),
            "provider_candidates": PROVIDER_CANDIDATES.get(key, [key]),
            "direction": "bidirectional",
            "criticality": CRITICALITY.get(key, "medium"),
            "data_classes": ["operational"],
            "credential_refs": [f"env:{key.upper()}_CREDENTIALS"],
            "sla": {"availability": "client-defined", "timeout_seconds": 30},
            "fallback_strategy": "queue-and-retry",
            "events": [],
            "commands": [],
        })
    return {"client_id": client_input["client_id"], "integrations": integrations}


def architecture_decisions(
    client_id: str, solution: dict[str, Any], evidence_ref: str = "solution/solution-contract.yaml"
) -> list[dict[str, Any]]:
    decisions = []
    for index, (domain, provider) in enumerate(sorted(solution.get("providers", {}).items()), start=1):
        decisions.append({
            "decision_id": f"ADR-{client_id}-{index:03d}",
            "client_id": client_id,
            "title": f"Select {provider['provider']} for {domain}",
            "status": "proposed",
            "context": f"Resolve provider for solution domain {domain}.",
            "decision": f"Use provider {provider['provider']} behind the {provider['type']} boundary.",
            "alternatives": [],
            "consequences": [
                "Provider-specific behavior remains behind an adapter.",
                "Replacement must not change canonical business contracts.",
            ],
            "affected_capabilities": [],
            "affected_domains": [provider["type"]],
            "evidence_refs": [evidence_ref],
            "approved_by": None,
            "approved_at": None,
        })
    return decisions
