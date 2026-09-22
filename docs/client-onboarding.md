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

Capture client-specific UX requirements in `input/client-input.yaml#experience_requirements`. Requirements may identify requested surfaces, screens, components and required states. A free-text UX requirement is allowed, but it remains unmapped and blocks client review until mapped or explicitly deferred/not-applicable.

Generate experience directions, prototype manifests and coverage:

`python -m tooling.experience.generator --client acme-retail`

For Medusa/Mercur/Tryton, unspecified behavior uses the governed standard core baseline. If the client brief changes a core behavior, record only the affected overlay in `input/client-input.yaml#core_module_requirements`.

Generate linked commerce/ERP/finance demo data:

`python -m tooling.prototype.demo_data --client acme-retail`

Generate the functional core-runtime plan:

`python -m tooling.prototype.core_runtime --client acme-retail`

Generate provider-specific seed bundles from the linked demo dataset:

`python -m tooling.prototype.seed_bundle --client acme-retail`

Provision the required real core services, apply the baseline plus client overlays, and import the applicable seed bundle. Then record health + seed evidence for each required module:

`python -m tooling.prototype.runtime_evidence --client acme-retail --provider medusa --health-ref <health-evidence> --seed-ref <seed-evidence>`

Repeat for Mercur and/or Tryton when required. Payments/logistics/messaging may use the governed mock scenario catalog during Phase C.

Verify the core runtime:

`python -m tooling.prototype.core_runtime --client acme-retail --check`

Generate an implementation-evidence plan for the selected direction:

`python -m tooling.experience.implementation --client acme-retail --direction a.yaml`

As prototype screens/components/states are implemented, mark them `implemented` in `a-implementation.yaml` with concrete source/runtime evidence references. Then check completeness:

`python -m tooling.experience.coverage --client acme-retail --direction a.yaml --check`

The check passes only when every UX-impacting client requirement is mapped and all required surfaces/screens/components/states have implementation evidence.

Create an immutable build/capture/review bundle:

`python -m tooling.review.session --client acme-retail --direction a.yaml --source-revision <git-sha> --created-by <actor>`

The Review Session command independently re-runs both gates. It refuses client review if UI coverage/implementation evidence is incomplete or if a required Medusa/Mercur/Tryton runtime lacks healthy evidence, linked demo data, or ready prototype provider bindings.

Create the immutable Prototype Revision for that exact build:

`python -m tooling.review.review_round create-revision --client acme-retail --review <REV-...yaml> --sequence 1 --created-by <actor>`

Create Review Round 001 around that revision:

`python -m tooling.review.review_round create-round --client acme-retail --revision <PROTO-...yaml> --review <REV-...yaml> --sequence 1`

During the client call, review feedback is captured as structured text with context. Example:

`python -m tooling.review.review_round add-feedback client-projects/acme-retail/feedback/rounds/<ROUND-...yaml> --surface customer-app --journey credit-order --screen checkout --component credit-limit-card --type visual --comment "Move available credit above payment options" --action request-change --created-by <client>`

The platform classifies visual/content feedback as a minor change routed to Nowa. Business-rule, integration, data, finance, security and workflow feedback is material and routes to a Change Contract. Approvals and discussion notes use the same Review Feedback contract.

After a minor change has a governed Nowa session, bind the feedback item to it:

`python -m tooling.review.review_round route-feedback <ROUND-...yaml> <FB-...yaml> --live-review-ref feedback/<LIVE-...yaml>`

For material feedback:

`python -m tooling.review.review_round route-feedback <ROUND-...yaml> <FB-...yaml> --change-contract-ref changes/<CHG-...yaml>`

Once the requested change is complete, resolve the feedback item:

`python -m tooling.review.review_round resolve-feedback <FB-...yaml>`

Record the QA evidence for the reviewed revision:

`python -m tooling.review.review_round record-qa <ROUND-...yaml> --qa-ref experience/visual-qa/<VQA-...yaml>`

Approve reviewed surfaces and journeys as the client confirms them:

`python -m tooling.review.review_round approve <ROUND-...yaml> --surface customer-app`

`python -m tooling.review.review_round approve <ROUND-...yaml> --journey credit-order`

Finalize the round:

`python -m tooling.review.review_round finalize <ROUND-...yaml>`

If changes are required, create Prototype Revision 002 with `--parent-revision-ref experience/revisions/<PROTO-001.yaml>`, create Review Round 002 with `--previous-round-ref feedback/rounds/<ROUND-001.yaml>`, and link the earlier round to the new revision with `link-next`. The loop can repeat for as many review rounds as needed.

Plan governed Visual + Business QA from the generated capture manifest:

`python -m tooling.review.visual_qa --client acme-retail --capture <CAP-...yaml>`

Review/QA records remain unapproved until humans and/or reviewer tooling have supplied concrete evidence.

For a Flutter client call, create a governed Nowa live-review session:

`python -m tooling.review.nowa_session create --client acme-retail --review-id <REV-...> --build-id <BLD-...> --started-by <actor> --participant <client> --output client-projects/acme-retail/feedback/LIVE-acme-retail-NOWA-001.yaml`

Record requested edits during the call:

`python -m tooling.review.nowa_session add-edit <LIVE-...yaml> --category spacing --summary "Reduce card spacing" --surface customer-app --target ProductCard.padding --before 24 --after 20 --git-path packages/agency_flutter_ui/lib/product_card.dart`

Minor visual/UX edits may then be persisted from Nowa into Flutter source and bound to a Git diff/revision:

`python -m tooling.review.nowa_session apply-minor <LIVE-...yaml> --edit-id EDIT-0001 --git-diff-ref <diff-or-pr-ref> --resulting-revision <git-sha>`

Material requests must be routed instead:

`python -m tooling.review.nowa_session route-material <LIVE-...yaml> --edit-id EDIT-0002 --change-contract-ref changes/CHG-002.yaml`

After the changed revision passes Visual QA:

`python -m tooling.review.nowa_session record-qa <LIVE-...yaml> --visual-qa-ref experience/visual-qa/<VQA-...yaml>`

Then record client confirmation:

`python -m tooling.review.nowa_session confirm <LIVE-...yaml> --confirmed-by <client-approver> --confirmed-at <ISO-8601>`

Material findings become Change Contracts. Unfinished Nowa sessions block scope freeze. After all review artifacts are approved and every Visual QA check is `pass`, freeze the immutable client scope:

`python -m tooling.review.freeze --client acme-retail --review <approved-review.yaml> --visual-qa <VQA-...yaml> --approved-by <client-approver> --approved-at <ISO-8601>`

The resulting `approved/scope-baseline.yaml` is the production handoff authority for A/B/C. It references the approved solution, experience direction, Review Session, Visual QA and Architecture Decision records.
