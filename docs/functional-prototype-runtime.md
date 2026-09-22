# Functional Prototype Runtime

Client review uses a functional solution prototype.

## Operating rule

The prototype is:

**standard core implementation + client-specific overlays + deterministic demo data + mock/sandbox external providers**

Core modules are not disposable mocks.

| Area | Prototype rule | Status in platform |
|---|---|---|
| Medusa commerce | Real standard core when commerce is in scope | Baseline + adapter + runtime gate implemented |
| Mercur marketplace | Real standard marketplace layer when marketplace/multi-vendor is in scope | Baseline + archetype/provider selection + runtime gate implemented |
| Tryton ERP | Real standard core when ERP/warehouse/accounting is in scope | Baseline + official container dependency + runtime gate implemented |
| Client-specific Medusa/Mercur/Tryton behavior | Overlay only affected baseline components | `core_module_requirements` implemented |
| Commerce/ERP demo data | Linked master, transaction, inventory and finance data | Deterministic dataset generator implemented |
| Payments | Mock/sandbox acceptable in prototype | Deterministic provider scenarios implemented |
| Logistics | Mock/sandbox acceptable in prototype | Deterministic provider scenarios implemented |
| WhatsApp/messaging | Mock/sandbox acceptable in prototype | Deterministic provider scenarios implemented |
| Core health | Required before Review Session | Enforced by review gate |
| UI completeness | Required before Review Session | Existing Phase-C completeness gate |

## Baseline/overlay behavior

If the client brief does not mention a Medusa/Mercur/Tryton component, the standard baseline remains unchanged.

If the brief contains an explicit core requirement, record it in:

`input/client-input.yaml#core_module_requirements`

Example:

```yaml
core_module_requirements:
  - requirement_id: REQ-CORE-021
    module: tryton
    target: warehouse.transfer
    change: require manager approval before inter-branch transfer
    source_refs: [brief:v3]
```

Only that target is treated as a client overlay. Other Tryton behavior remains standard.

## Demo data

`tooling.prototype.demo_data` creates linked demo data covering:
- B2C and B2B customers
- products, warehouses, suppliers and sellers
- successful and failed orders
- approvals and business credit
- partial fulfilment
- inventory shortage
- returns and refunds
- purchases
- marketplace settlements
- customer invoices
- receivables/payables
- GST-bearing accounting entries
- COGS/inventory entries
- reconciliation matches and mismatches

The same identifiers should be visible across UI, commerce, marketplace, ERP, operations and analytics.

## External mocks

`tooling.prototype.mock_providers.MockProviderRuntime` provides deterministic scenarios for Razorpay, Cashfree, Shiprocket, Delhivery and WhatsApp.

These mocks simulate the provider edge only. Internal order, inventory, ERP and finance consequences remain real core-system behavior.

## Seed the core runtimes

Generate provider-specific seed bundles from the governed demo dataset:

`python -m tooling.prototype.seed_bundle --client <client-id>`

This produces Medusa, Mercur and Tryton seed payloads under:

`experience/fixtures/provider-seeds/`

After importing the applicable seed into the actual core runtime, record both health and seed evidence:

`python -m tooling.prototype.runtime_evidence --client <client-id> --provider medusa --health-ref <ref> --seed-ref <ref>`

Repeat for every required core module. A runtime is not considered client-review ready merely because the service process is up; it must also be seeded with the governed prototype data.

## Client-review gate

A Review Session may open only when:

1. required UI screens/components/states have implementation evidence;
2. required Medusa/Mercur/Tryton modules are healthy and have runtime evidence;
3. the linked demo dataset is schema-valid and ready;
4. required external prototype providers have ready mock/sandbox/live bindings.

This prevents a UI-only prototype from being presented as a functional solution.

## Environment boundary

The repository now governs standard baselines, overlays, deterministic data, provider mocks, dependency composition and readiness gates. Medusa/Mercur application projects are provisioned through their upstream project tooling; they are not vendored copies inside PinCommerce. Runtime health evidence must come from the actual provisioned environment before client review.
