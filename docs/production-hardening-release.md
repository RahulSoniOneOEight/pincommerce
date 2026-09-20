# Production Hardening & Release

Part 4 introduces exact-candidate release governance.

## Release path

Source revision
→ immutable Release Candidate
→ hardening evidence
→ staging deployment/validation
→ observability evidence
→ UAT
→ explicit human Production Authorization
→ promote exact candidate
→ production smoke
→ telemetry watch
→ release record
→ recovery/rollback if required

## Candidate identity

A release candidate contains:
- source revision
- aggregate artifact digest
- per-component SHA-256 digest
- immutable flag
- client/environment identity

The artifact validated in staging must be the artifact promoted to production.

## Hardening gates

Baseline checks include:
- contract/unit/integration/E2E validation
- secrets/authz/tenant isolation
- dependency vulnerability review
- performance budget
- accessibility
- migration safety
- backup/recovery
- observability
- reconciliation
- provider health

Blocking policy: `pass` is acceptable; `warning` is blocking unless the check id is explicitly
declared in `non_blocking_checks`; `fail` and `not-run` are blocking; an unknown status is an error.
A required check that is **omitted** from a hardening record is treated as `not-run` and is blocking,
and an unknown check id is blocking — so a hardening record can never pass by silently dropping
checks.

## Human gates

UAT and Production Authorization remain explicit human controls. OpenCode/ChatGPT/DeepSeek can prepare evidence and identify risks, but cannot authorize production.

## Recovery

Every release should have a recovery strategy such as rollback, roll-forward, restore or feature disablement.

The reference-retail release files are contract fixtures/examples only. They do not claim that a real external production system was deployed.
