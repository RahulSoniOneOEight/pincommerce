# Universal Review

The review subsystem generalizes the existing Flutter review model across surfaces.

The canonical, CI-validated review contract is the **Review Session**
(`contracts/schemas/review-session.schema.json`). `review/artifact-contract.md` describes a
legacy artifact shape and is not validated. See `docs/governance-status.md`.

A review session identifies:
- client and surface
- route/screen
- environment and build identity
- journey and direction
- viewport
- screenshot/live preview
- comments and approval state

Material feedback must be converted into a Change Contract before production implementation.


## Prototype Revision and Review Round

A Review Session is the evidence/approval envelope for one immutable build. It now participates in a higher-level iteration model:

`Prototype Revision → Review Round → Feedback → Changes → Next Prototype Revision`

Prototype Revision records the exact build/source revision plus prototype coverage, implementation evidence and functional-core references.

Review Round records one client review iteration against exactly one Prototype Revision. Text feedback is captured as Review Feedback with surface/journey/screen/component context. The feedback text remains human-readable, while classification and routing are structured:

- visual/content request → minor change → Nowa
- business rule/integration/data/finance/security/workflow request → material change → Change Contract
- approve → approval/no routing
- discuss → discussion

The final Review Round must be approved, all feedback resolved, all required surfaces/journeys approved and QA evidence attached before scope freeze.
