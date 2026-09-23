# Real Phase E1 staging execution

The `Execute Phase E1 Staging` workflow is the environment-bound execution path after the Phase E1 governance pipeline.

It checks out the **exact source SHA supplied by the operator**, verifies HEAD equals that SHA, rebuilds the immutable candidate identity from the committed Phase-D package, generates the staging manifest, collects live environment evidence and runs the strict E1 gate.

## Required staging environment bindings

Configure these as GitHub **staging environment secrets** rather than repository files:

- `STAGING_RUNTIME_ENDPOINTS_JSON` — map runtime IDs such as `commerce`, `erp`, `search`, `support`, `automation`, `database`, `experience_web` to health/readiness URLs.
- `STAGING_RUNTIME_ATTESTATIONS_JSON` — non-HTTP evidence such as mobile build/smoke status. Each entry must contain `{"status":"pass","evidence":"..."}`.
- `STAGING_IMPORT_PROBES_JSON` — map each manifest import ID to a read-back verification endpoint.
- `STAGING_E2E_PROBES_JSON` — map each required cross-domain journey ID to an E2E verification endpoint.
- `STAGING_OBSERVABILITY_PROBES_JSON` — URLs for `metric`, `trace`, `error`, and `alert` verification.
- Provider bindings:
  - `RAZORPAY_STAGING_URL`, `RAZORPAY_STAGING_AUTH`
  - `SHIPROCKET_STAGING_URL`, `SHIPROCKET_STAGING_AUTH`
  - `WHATSAPP_STAGING_URL`, `WHATSAPP_STAGING_AUTH`

A missing runtime, import/read-back, E2E, provider or observability binding produces blocked evidence. There is no default success path.

## Evidence package

A successful run uploads a 30-day GitHub Actions artifact containing:
- exact release candidate
- staging manifest
- runtime evidence
- data import/read-back evidence
- cross-system E2E evidence
- provider sandbox/staging evidence
- observability evidence
- final `staging-validation.yaml`

The final validation must reference the exact candidate and the candidate digest must match the staging manifest.

## Boundary

This workflow executes and verifies an already-provisioned staging environment through explicit deployment bindings. It does not invent infrastructure credentials or create human UAT/Production Authorization. UAT and production authorization remain E2/E3 human gates.
