# Phase 2 — Production, Operations and Learning

Phase 2 extends the existing Phase D, E1 and release machinery. It does not replace it.

## Goal

Move an approved Phase 1 integrated prototype through production readiness, hardening,
staging, human UAT, human production authorization, exact-candidate release, operations,
recovery and governed continuous improvement.

## Existing capabilities reused

- production plan/readiness/execution and cross-domain QA
- immutable release candidates
- strict hardening evidence
- E1 staging evidence
- provider sandbox evidence
- observability evidence
- UAT records
- production authorization
- exact-candidate release gates
- release and recovery records

## New control plane

`python -m tooling.orchestrator.phase2 --client <client>`

Use `--write` to persist the assessment at
`client-projects/<client>/release/phase2-readiness.yaml`.

Use `--check` for a strict gate. It exits non-zero until the exact candidate has
passed the release gate or is already operating.

The orchestrator is evidence-reading by design. Missing evidence is a blocker; it is
never synthesized into a passing record.

## Human authority

UAT and production authorization are hard human gates. Automation may prepare evidence,
surface blockers and execute already-authorized technical steps, but it cannot infer or
manufacture either approval.

## Status model

- `phase2-not-ready`: prerequisites/evidence incomplete
- `production-ready`: hardened/staged/observable but human release gates incomplete
- `release-authorized`: exact candidate passed UAT and production authorization
- `operating`: release record and operational evidence exist

Continuous improvement produces governed proposals. It never rewrites client truth or
approved scope silently.
