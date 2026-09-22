# Functional Prototype Runtime

Phase C client review uses a functional solution prototype, not a UI-only mock.

## Core rule

- Medusa commerce is a real core runtime when commerce is in scope.
- Mercur is the standard marketplace layer when a marketplace/multi-vendor business model is in scope. Mercur extends Medusa.
- Tryton is a real ERP runtime when ERP/warehouse/accounting is in scope.
- Client brief requirements override only the affected baseline components. Everything else stays on the governed standard baseline.
- Payments, logistics, WhatsApp and other external providers may use deterministic mock or sandbox adapters at prototype stage.
- Demo master, transaction and finance data must be linked across commerce and ERP.

## Dependencies

Start common dependencies and the standard Tryton container:

`docker compose -f infrastructure/prototype/docker-compose.dependencies.yml up -d`

Medusa and Mercur application projects are provisioned from their official project tooling rather than vendored into PinCommerce. This repository governs their baseline configuration, client overlays, health evidence and review readiness. Do not mark a client prototype ready until the generated `prototype-core-runtime.yaml` records healthy evidence for every required core module.

Mercur already extends Medusa. For marketplace clients, provision the Mercur project as the marketplace/commerce runtime instead of starting a conflicting second Medusa API on the same port.

## Governed commands

Generate standard demo data:

`python -m tooling.prototype.demo_data --client <client-id>`

Generate the core runtime plan:

`python -m tooling.prototype.core_runtime --client <client-id>`

Generate provider-specific seed bundles:

`python -m tooling.prototype.seed_bundle --client <client-id>`

After importing the applicable seed bundle into the actual Medusa/Mercur/Tryton runtime, record health and seed evidence:

`python -m tooling.prototype.runtime_evidence --client <client-id> --provider <medusa|mercur|tryton> --health-ref <ref> --seed-ref <ref>`

Then check readiness:

`python -m tooling.prototype.core_runtime --client <client-id> --check`

Client Review creation also executes this gate.
