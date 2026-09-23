# Phase D1 — Approved Scope to Production Plan

Phase D1 converts the approved Phase-C authority into a deterministic production implementation plan.

## Authority

The compiler starts from:

`approved/current-scope.yaml`

It resolves the immutable baseline referenced by that pointer. It does not reinterpret the original client brief.

The approved baseline supplies the included/deferred/excluded scope and accepted architecture decisions. The compiler then resolves the approved Solution, Business and Data Contracts plus governed derived maps.

## Outputs

`python -m tooling.production.compiler --client <client>`

writes:

- `production/production-plan.yaml`
- `production/runtimes.yaml`
- `production/integrations.yaml`
- `production/configuration.yaml`
- `production/data-migration.yaml`
- `production/acceptance.yaml`

The master plan records:
- exact approved scope baseline
- every approved capability and its production owner
- every required surface and runtime
- production runtime/provider mapping
- external integration transition from prototype/mock to live
- credential references
- canonical data ownership
- migration/opening-data strategy
- approved overlays
- deferred/excluded scope
- required production acceptance checks

## Explicit provider selection

The compiler never silently chooses between multiple approved connector candidates.

When an integration has several candidates, Phase D1 remains blocked until an explicit production selection is supplied in:

`production/provider-selections.yaml`

Example:

```yaml
integrations:
  payment: razorpay
  logistics: shiprocket
  whatsapp: meta-whatsapp-cloud
runtime_versions:
  experience_mobile: "<exact Flutter pin>"
  experience_web: "<exact Next.js pin>"
  commerce: "<exact Medusa pin>"
  erp: "<exact Tryton pin>"
  search: "<exact Meilisearch pin>"
  support: "<exact Chatwoot pin>"
  automation: "<exact Activepieces pin>"
  database: "<exact PostgreSQL pin>"
```

A single approved candidate may resolve automatically.

Production runtime versions are also D1 operational inputs in this file. This keeps version pinning out of the already-approved Phase-C Solution Contract.

## Production readiness

`python -m tooling.production.readiness --client <client> --write`

checks:
- approved scope resolution
- capability ownership
- runtime/provider mapping
- runtime version pinning
- surface production mapping
- integration provider selection
- credential inventory
- canonical data ownership
- migration strategy
- deferred-scope exclusion
- production test plan

The gate returns `production-ready` only when every check passes.

A provider version left as `null` in the prototype Solution Contract is deliberately blocking in D1. Production versions must be explicitly pinned rather than silently inheriting a floating/default version.

## Operating rule

```text
Phase C
WHAT was approved?
        ↓
approved/current-scope.yaml
        ↓
Phase D1
HOW will that exact approved scope be built in production?
        ↓
production/production-plan.yaml
        ↓
production-readiness.yaml
        ↓
D2 provisioning
```

The compiler follows:

`standard baseline + approved overlays + explicit production providers + production data strategy`

Prototype demo data is always marked for replacement; it is never promoted as production data.
