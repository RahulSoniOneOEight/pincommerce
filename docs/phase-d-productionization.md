# Phase D — Productionization

Phase D converts the immutable approved Phase-C scope into a production-ready implementation package. It ends before UAT and production authorization, which remain Phase E human/release gates.

## D1 — Production plan and readiness

Authority:
`approved/current-scope.yaml → immutable BASE-vN → production/production-plan.yaml`

The compiler maps approved capabilities, surfaces, runtime providers, integration providers, canonical data ownership, migration strategy and production tests. Runtime versions and external provider selections are explicit D1 inputs.

## D2 — Runtime provisioning contract

Every required runtime has:
- exact provider/version or immutable source pin
- provisioning mode
- healthcheck
- evidence reference
- validated status

Reference-retail validates Medusa, Tryton, PostgreSQL and Meilisearch in the Phase-D CI acceptance workflow. Web/Flutter build evidence comes from the normal platform validation workflow. Chatwoot and Activepieces are validated at the adapter contract boundary; their live deployment is environment-specific.

## D3 — Production provider bindings

Reference-retail selects:
- payments: Razorpay
- logistics: Shiprocket
- messaging: Meta WhatsApp Cloud

Credentials are environment references only; no secrets are committed. Provider adapter contracts are tested in D. Calls requiring real external credentials are deliberately marked for live verification in staging (Phase E), rather than fabricating live evidence.

## D4 — Migration readiness

The migration plan requires:
- prototype/demo data replacement
- master-data identity mapping
- opening inventory load/reconciliation
- opening finance load/reconciliation

The reference client performs deterministic migration-mechanics validation. This does **not** claim real client production data was migrated.

## D5 — Cross-domain integration QA

The gate requires passing journeys across:
- experience → commerce → payments → ERP
- commerce → ERP → finance
- commerce → logistics → ERP
- return/refund
- integration exceptions → ops/analytics

Idempotency, bounded retry, dead-letter handling and reconciliation are mandatory.

## D6 — Production QA

Production QA combines contract validation, unit/integration tests, cross-domain QA, runtime health, provider adapter contracts, migration safety, reconciliation, security/secrets checks, and web/Flutter build evidence.

## Completion boundary

`python -m tooling.production.execution --client reference-retail`

returns `status: complete` only when D1–D6 pass with zero blockers.

Phase D completion means the implementation package is ready to enter staging/UAT. It does not mean a real client production deployment has occurred, and it cannot bypass Phase E UAT or Production Authorization.
