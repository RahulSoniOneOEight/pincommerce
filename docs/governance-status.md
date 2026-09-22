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
| Design Contract | `design-contract/` | Partial | Required files present; no token/component JSON Schema yet |
| Integration Contract | `platform/integration/*.yaml`, `contracts/schemas/provider-adapter.schema.json` | Partial | Catalogs present; provider adapters schema-validated; unified integration schema pending |
| Data Contract | `contracts/schemas/data-contract.schema.json`, `client-projects/*/contracts/data-contract.yaml` | Enforced now | Schema-validated reference instance; defines canonical entity ownership |
| Business Contract | `contracts/schemas/business-contract.schema.json`, `client-projects/*/contracts/business-contract.yaml` | Enforced now | Schema-validated reference instance |
| Change Contract | `contracts/schemas/change-contract.schema.json`, `client-projects/*/changes/` | Enforced now | Schema-validated reference instance |

## Review contracts

| Contract | Location | Status | Enforcement |
|---|---|---|---|
| Review Session | `contracts/schemas/review-session.schema.json`, `client-projects/*/feedback/` | Enforced now | Reference instance schema-validated in CI |
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
| Scope Baseline | `contracts/schemas/scope-baseline.schema.json`, `client-projects/*/approved/scope-baseline.yaml` | Enforced now | Immutable client scope freeze; creation requires approved Review Session and passing Visual QA |

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
