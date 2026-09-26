# Phase 1 Steps 1–45 — Design-first completion gate

This layer makes the pre-build experience lifecycle measurable. It does not claim that a client is complete merely because schemas or generated YAML exist.

## Hard rules

1. Every declared reference must be inspected and reduced to evidenced patterns. No `pending-analysis` reference can pass.
2. Every extracted pattern receives REUSE, ADAPT, COMBINE, MODERNIZE, REJECT or BUILD_NEW.
3. Detailed journeys require executable nodes with success/error transitions.
4. A client-facing design review requires a Penpot-backed design revision, Design IR, component contracts and visual QA.
5. Builders cannot self-approve. Human Review Round approval is required.
6. Experience approval is immutable and bound to design revision, source revision, prototype revision and review round.
7. Production UI work must consume the approved experience baseline; changing approved upstream design invalidates downstream approval.

## Review package

The human-facing package contains Overview, Directions, Design System, Screens, Journeys, Responsive, States, References, QA, Feedback and Approval. Review Mode should render these as one review experience; the repository remains the machine authority.

## Commands

Create the governed review package:

    python -m tooling.review.design_review package --client <client> --design-revision <revision> --source-revision <git-sha> --penpot-ref <penpot-project-or-revision>

After the Review Round has approved every required surface and journey and QA has been recorded:

    python -m tooling.review.design_review approve --client <client> --package <DRP-file.yaml> --prototype-revision-ref <path> --review-round-ref <path> --approved-by <human> --approved-at <timestamp>

Strictly assess all 45 pre-build steps:

    python -m tooling.orchestrator.phase1_45 --client <client> --check

A non-zero exit means the client is not allowed to claim Steps 1–45 complete. External design systems such as Penpot still require valid credentials and a real project/revision; the gate deliberately does not fabricate them.
