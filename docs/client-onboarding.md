# Client Onboarding Runbook

## 1. Initialize the workspace

Example:

`python -m tooling.onboarding.init_client --client acme-retail --industry retail --business-model d2c --business-model b2b --capability catalogue --capability checkout --integration payment --integration logistics --geography india`

This creates:
- input/client-input.yaml
- workflow/workflow-state.yaml
- standard derived/solution/experience/feedback/change/approval/production/QA/UAT/release directories

## 2. Complete and validate intake

Edit the structured client input with the information gathered during discovery.

Validate:

`python -m tooling.contracts.validator client-input client-projects/acme-retail/input/client-input.yaml`

## 3. Advance intake stage

`python -m tooling.workflow.runtime advance --client acme-retail --actor <name>`

## 4. Generate the baseline delivery blueprint

Preview:

`python -m tooling.onboarding.engine --client acme-retail --print-only`

Write artifacts:

`python -m tooling.onboarding.engine --client acme-retail`

Outputs include:
- Client Truth Register with facts, assumptions, unknowns and conflicts
- normalized client profile
- evidence-backed industry/archetype classification
- benchmark report
- canonical capability gap plus prioritized impact/severity analysis
- reuse decisions
- capability map
- journey map
- entity map
- surface map
- integration map with provider candidates, SLA/fallback/credential metadata
- dependency map
- draft Solution Contract
- proposed Architecture Decision Records for provider choices

## 5. Human/strategy review

The generated blueprint is a deterministic baseline, not automatic client approval. Strategy/architecture review may:
- accept recommendations
- classify capabilities as later/not applicable
- add missing client-specific capabilities
- override provider candidates
- record exclusions and rationale

Only reviewed artifacts should progress toward experience directions and production contracts.


## 6. Complete the A/B/C experience and freeze

Generate experience directions and prototype manifests:

`python -m tooling.experience.generator --client acme-retail`

Create an immutable build/capture/review bundle:

`python -m tooling.review.session --client acme-retail --direction a.yaml --source-revision <git-sha> --created-by <actor>`

Plan governed Visual + Business QA from the generated capture manifest:

`python -m tooling.review.visual_qa --client acme-retail --capture <CAP-...yaml>`

Review/QA records remain unapproved until humans and/or reviewer tooling have supplied concrete evidence. Material findings become Change Contracts. After all review artifacts are approved and every Visual QA check is `pass`, freeze the immutable client scope:

`python -m tooling.review.freeze --client acme-retail --review <approved-review.yaml> --visual-qa <VQA-...yaml> --approved-by <client-approver> --approved-at <ISO-8601>`

The resulting `approved/scope-baseline.yaml` is the production handoff authority for A/B/C. It references the approved solution, experience direction, Review Session, Visual QA and Architecture Decision records.
