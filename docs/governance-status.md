# Contract & Governance Status

This document is the single source of truth for **which governance artifacts are enforced
today** and which are roadmap. If another document implies enforcement that is not listed
here as "Enforced now", this document wins.

Legend:
- **Enforced now** — schema/instance validated by `python tooling/validation/validate_all.py` in CI.
- **Partial** — presence is checked and/or a schema exists, but instances are not fully validated.
- **Roadmap** — documented intent only; no enforcement yet.
- **Legacy** — superseded; retained for history, not validated.

## Production contracts

| Contract | Location | Status | Enforcement |
|---|---|---|---|
| Solution Contract | `contracts/schemas/solution-contract.schema.json`, `client-projects/*/solution/` | Enforced now | JSON Schema validation of the reference instance; generated deterministically by `tooling.onboarding.engine` (drift-checked) |
| Design Contract | `contracts/schemas/design-contract.schema.json`, `client-projects/*/contracts/design-contract.yaml`, `design-contract/` | Enforced now | Schema-validates source provenance, tokens/theme, approved components, icons, motion and Flutter/web bindings; required by the pre-production completion gate |
| Integration Contract | `contracts/schemas/integration-contract.schema.json`, `client-projects/*/contracts/integration-contract.yaml`, `platform/integration/*.yaml` | Enforced now | Unified schema binds provider adapters, commands/events, retry, reconciliation, credential references, SLA and fallback; required by the pre-production completion gate |
| Data Contract | `contracts/schemas/data-contract.schema.json`, `client-projects/*/contracts/data-contract.yaml` | Enforced now | Schema-validated reference instance; defines canonical entity ownership |
| Business Contract | `contracts/schemas/business-contract.schema.json`, `client-projects/*/contracts/business-contract.yaml` | Enforced now | Schema-validated reference instance |
| Change Contract | `contracts/schemas/change-contract.schema.json`, `client-projects/*/changes/` | Enforced now | Schema-validated reference instance |

## Review contracts

| Contract | Location | Status | Enforcement |
|---|---|---|---|
| Review Session | `contracts/schemas/review-session.schema.json`, `client-projects/*/feedback/` | Enforced now | Review build/surface/journey approval envelope |
| Prototype Revision | `contracts/schemas/prototype-revision.schema.json`, `client-projects/*/experience/revisions/` | Enforced now | Immutable V1/V2/V3 prototype identity bound to exact build/source/coverage/runtime evidence |
| Review Round | `contracts/schemas/review-round.schema.json`, `client-projects/*/feedback/rounds/` | Enforced now | Explicit client review iteration around one Prototype Revision |
| Review Feedback | `contracts/schemas/review-feedback.schema.json`, `client-projects/*/feedback/items/` | Enforced now | Structured text feedback with surface/journey/screen/component context and governed routing |
| Review Artifact | `contracts/schemas/review-artifact.schema.json`, `review/artifact-contract.md` | Legacy | Superseded by Review Session; no instance, not validated |
| Visual QA | `contracts/schemas/visual-qa.schema.json`, `client-projects/*/experience/visual-qa/VQA-*.yaml` | Enforced now | Reference instance schema-validated in CI; scope freeze requires passed checks |
| Live Client Review (Nowa) | `contracts/schemas/live-review-session.schema.json`, `client-projects/*/feedback/LIVE-*.yaml` | Enforced now | Minor edits require Git revision + post-change QA; material edits must route to Change Contract; unfinished sessions block scope freeze |
| Prototype Coverage | `contracts/schemas/prototype-coverage.schema.json`, `client-projects/*/experience/prototypes/*-coverage.yaml` | Enforced now | Client UX requirements must map to surfaces/screens/components/states; unmapped requirements block Review Session creation |
| Prototype Implementation Evidence | `contracts/schemas/prototype-implementation.schema.json`, `client-projects/*/experience/prototypes/*-implementation.yaml` | Enforced at review gate | Every required screen/component/state must have implemented evidence before client review |
| Prototype Core Runtime | `contracts/schemas/prototype-core-runtime.schema.json`, `client-projects/*/experience/prototype-core-runtime.yaml` | Enforced at review gate | Required Medusa/Mercur/Tryton modules must be healthy with runtime evidence; client overlays are explicit |
| Prototype Demo Dataset | `contracts/schemas/prototype-demo-dataset.schema.json`, `client-projects/*/experience/fixtures/*-demo-dataset.yaml` | Enforced at review gate | Linked commerce/ERP/finance demo data must be ready before functional client review |

The canonical review model is **Review Session**. The review pipeline in
`docs/review-visual-validation.md` (Build Identity → Capture Manifest → Review Session →
BugDrop → Change Contract when material) is authoritative.

## Release evidence

| Artifact | Location | Status | Enforcement |
|---|---|---|---|
| Release Candidate | `contracts/schemas/release-candidate.schema.json`, `client-projects/*/release/candidates/` | Enforced now | Schema-validated; exact-candidate gate |
| Hardening Evidence | `contracts/schemas/hardening-evidence.schema.json` | Enforced now | Schema-validated; strict blocking policy in `tooling.release.hardening` |
| Staging Validation | `contracts/schemas/staging-validation.schema.json` | Enforced now | Schema-validated; required by the release gate |
| Observability Evidence | `contracts/schemas/observability-evidence.schema.json` | Enforced now | Schema-validated; required by the release gate |
| UAT Record | `contracts/schemas/uat-record.schema.json` | Enforced now | Schema-validated; human approver required |
| Production Authorization | `contracts/schemas/production-authorization.schema.json` | Enforced now | Schema-validated; human authorizer required |
| Release Record / Recovery Record | `contracts/schemas/release-record.schema.json`, `recovery-record.schema.json` | Enforced now | Schema-validated |

The release gate (`tooling.release.gates.verify_release_readiness`) requires the exact same
`candidate_id` across candidate, hardening, staging, observability, UAT and authorization, and
rejects a missing or failing staging validation.

## AI proposals

| Artifact | Location | Status | Enforcement |
|---|---|---|---|
| AI Proposal | `contracts/schemas/ai-proposal.schema.json`, `client-projects/*/intelligence/ai/` | Enforced now | Reference instance schema-validated; human review recorded |
| AI Decision | `contracts/schemas/ai-decision.schema.json`, `client-projects/*/intelligence/ai/decisions/` | Enforced now | Written only by the promotion gate |
| AI promotion | `tooling.ai.proposals promote` | Enforced now | Guarded gate: requires an explicit human promoter **and** an approved/modified human review; validates the proposal and the decision record against schema; records audit evidence |

AI output is advisory. The promotion gate never writes to governed truth (`derived/*`,
`solution/*`); it records a decision in the `intelligence/ai/decisions/` ledger. Changing
governed artifacts remains a human/deterministic step (edit `input/client-input.yaml` and re-run
the onboarding engine). See `docs/ai-operating-model.md`.


## A/B/C completion authorities

| Artifact | Location | Status | Enforcement |
|---|---|---|---|
| Client Truth Register | `contracts/schemas/truth-register.schema.json`, `client-projects/*/derived/truth-register.yaml` | Enforced now | Schema-validated reference instance; facts/assumptions/unknowns/conflicts remain explicit |
| Classification Evidence | `client-projects/*/derived/classification-evidence.yaml` | Enforced by drift | Deterministic business-model → archetype evidence generated by onboarding engine |
| Capability Gap Analysis | `client-projects/*/derived/capability-gap-analysis.yaml` | Enforced by drift | Prioritized impact/severity view generated alongside canonical gap artifact |
| Integration Map | `contracts/schemas/integration-map.schema.json`, `client-projects/*/derived/integration-map.yaml` | Enforced now | Schema-validated; provider candidates, criticality, SLA/fallback and credential refs |
| Architecture Decision | `contracts/schemas/architecture-decision.schema.json`, `client-projects/*/solution/decisions/` | Enforced now | Reference ADR schema-validated; generated provider choices remain proposed until human acceptance |
| Scope Baseline | `contracts/schemas/scope-baseline.schema.json`, `client-projects/*/approved/scope-baselines/` | Enforced now | Immutable versioned client scope freeze; creation requires approved Review Session/Review Round and passing QA |
| Current Scope Pointer | `contracts/schemas/current-scope.schema.json`, `client-projects/*/approved/current-scope.yaml` | Enforced now | Mutable pointer to the latest approved immutable baseline; historical baseline files are never overwritten |

The A/B/C authority chain is:

```text
client-input.yaml
→ truth-register.yaml
→ client-profile / classification / benchmark
→ capability-gap + prioritized gap analysis
→ capability / journey / entity / surface / integration / dependency maps
→ solution-contract + architecture decisions
→ experience directions + prototype
→ capture + Visual QA
→ Review Session + Change Contract
→ immutable scope-baseline.yaml
```

AI remains advisory throughout this chain. A generated classification or architecture decision does not become approved client scope without the applicable human review/freeze gate.


## A/B/C seamless completion gate

The final A/B/C scope freeze now re-validates the whole authority chain rather than trusting an approved Review Session in isolation.

It blocks when:
- Client Truth still contains unresolved assumptions, unknowns, questions or conflicts;
- active Architecture Decisions remain proposed/rejected instead of accepted;
- prototype coverage or implementation evidence has changed or become incomplete;
- a required Medusa/Mercur/Tryton core runtime is not healthy/seeded;
- required surfaces or journeys are not explicitly approved;
- any required surface lacks passing Visual + Business QA;
- any mandatory QA check is missing;
- a live-review session attached to the selected Review Session is unfinished or contains unrouted material changes.

Unrelated historical/live-review sessions no longer block a later review round merely because they exist in the feedback directory.

Use `python -m tooling.validation.abc_seam --client <client> --direction a.yaml` to inspect A/B/C readiness before attempting client review/freeze.


## Phase D1 production planning

| Artifact | Location | Status | Enforcement |
|---|---|---|---|
| Production Plan | `contracts/schemas/production-plan.schema.json`, `client-projects/*/production/production-plan.yaml` | Enforced now | Compiled from `approved/current-scope.yaml`; maps approved capabilities, surfaces, runtimes, integrations, data and overlays |
| Production Migration Plan | `contracts/schemas/production-migration-plan.schema.json`, `client-projects/*/production/data-migration.yaml` | Enforced now | Demo replacement, master migration, opening inventory and opening finance strategy |
| Production Readiness | `contracts/schemas/production-readiness.schema.json`, `client-projects/*/production/production-readiness.yaml` | Enforced now | Blocks D2 when scope, provider selection, runtime pinning, credentials, data ownership, migration or test planning is incomplete |

Phase D1 consumes the immutable baseline referenced by `approved/current-scope.yaml`. It does not re-interpret the original brief. Multiple connector candidates require an explicit production selection; prototype runtimes with unpinned versions are deliberately blocked until a production version is selected.


## Complete Phase D productionization

Phase D is complete only when all D1–D6 gates pass with zero blockers.

| Stage | Authority | Enforced result |
|---|---|---|
| D1 Production Plan | `production/production-plan.yaml` + `production/production-readiness.yaml` | Approved scope compiles without unresolved capabilities, runtimes, providers, credentials or migration/test strategy |
| D2 Runtime Provisioning | `production/production-execution.yaml` | Every required runtime has a pinned version/source, provisioning mode, healthcheck and evidence |
| D3 Provider Bindings | `production/production-execution.yaml` | Selected external providers map to governed adapters and credential references; live credential calls are deferred to staging rather than fabricated |
| D4 Migration Readiness | `production/data-migration.yaml` + `qa/migration-validation.yaml` | Demo data is explicitly replaced and master/opening inventory/opening finance mechanics are validated |
| D5 Cross-domain QA | `qa/cross-domain.yaml` | Commerce/payment/ERP/logistics/refund/ops flows pass idempotency, retry, dead-letter and reconciliation checks |
| D6 Production QA | `qa/production-qa.yaml` | Contracts, tests, runtime health, migration safety, security and build evidence pass |
| Phase D Completion | `production/phase-d-completion.yaml` | `python -m tooling.production.execution --client <client>` returns `status: complete` |

Reference-retail is a governed reference acceptance. Contract-tested external provider bindings require real credential/live verification in Phase E staging. Phase D completion does not represent a real client production deployment and cannot bypass UAT or Production Authorization.


## Pre-production points 1–40 completion

The authoritative platform-completion gate before Phase D is:

`python -m tooling.validation.preproduction --client <client> --check-drift`

It reuses the A/B/C seam and prototype coverage gates, validates the Design and Integration
Contracts, component-selection and design-learning evidence, approved visual baseline binding,
design-debt policy, accepted architecture decisions, immutable scope pointer/baseline, and the
client's persisted completion manifest.

The reference-retail acceptance manifest is
`client-projects/reference-retail/approved/preproduction-completion.yaml`. It contains exactly
40 passing point records and is immutable. CI rejects drift between current governed inputs and
that approved completion manifest.

This gate establishes **platform completeness through scope freeze**. It does not fabricate
client credentials or represent Phase D/E deployment, UAT or production authorization.
