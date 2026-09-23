# Phase E1 — Exact-candidate staging and evidence

Phase E1 converts a Phase-D-complete package into an immutable staging candidate and refuses progression until runtime, data, E2E, provider and observability evidence all reference the exact same candidate.

## Authority chain

`main/source SHA → Phase-D artifacts → Release Candidate digest → Staging Manifest → runtime/import/E2E/provider/observability evidence → staging-validation.yaml`

The candidate digest is calculated over the governed Phase-D production plan, readiness, execution, completion and QA artifacts. The staging manifest copies the candidate ID, digest and source revision. Any mismatch is blocking.

## Required evidence

E1 requires all of the following:
- required staging runtimes healthy
- required data imports completed **and read back**
- every required cross-domain flow passed
- every selected live provider passed a sandbox/staging probe
- observability contains passing metric, trace, error-path and alert evidence

A missing provider secret is not treated as success. The provider evidence becomes `blocked`, which prevents `staging-validation.yaml` from passing.

## Provider probes

`tooling.staging.provider_probe` consumes environment-bound URLs and authorization values:

- `RAZORPAY_STAGING_URL`, `RAZORPAY_STAGING_AUTH`
- `SHIPROCKET_STAGING_URL`, `SHIPROCKET_STAGING_AUTH`
- `WHATSAPP_STAGING_URL`, `WHATSAPP_STAGING_AUTH`

The URLs are deployment bindings rather than hard-coded provider endpoints so API/version/auth changes do not require changing governance contracts. Secrets must remain in the staging environment/GitHub environment secrets.

## Human boundary

E1 can produce `staging-validation: passed`, but it cannot approve UAT or Production Authorization. Those remain explicit human gates in E2/E3.
