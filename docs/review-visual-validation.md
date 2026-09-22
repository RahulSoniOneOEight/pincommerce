# Review & Visual Validation

## Flow

Immutable Build Identity
→ Capture Manifest
→ Screenshot/Preview Evidence
→ Visual QA
→ Review Session
→ Nowa Live Client Review (Flutter, when used)
→ post-change Visual QA
→ BugDrop
→ Change Contract when material
→ Rebuild / Re-review

## Build identity

Every review is tied to a source revision and direction. Review comments therefore cannot drift between builds.

## Capture manifest

The capture plan enumerates:
- surface
- runtime
- viewport
- deterministic state
- expected evidence path

Flutter defaults to a mobile viewport. Web captures desktop and mobile targets. External/provider surfaces may be represented by external evidence until an Agency-owned extension exists.

## BugDrop routing

Visual/UX/content issues remain in the experience loop unless severity or impact requires formal change control.

Business-rule, integration, data, security, performance and accessibility findings route to Change Contract review.

## AI visual review

OpenCode routes screenshot review to the Visual Review Agent, with ChatGPT preferred for reviewer reasoning. AI findings remain proposals/BugDrops and must reference concrete artifacts.


## Nowa live client review

For Flutter client calls, Nowa is the approved live visual-refinement environment.

A live session must be recorded as `feedback/LIVE-*.yaml` using the `live-review-session` contract.

Minor live-edit categories:
- spacing
- layout
- typography
- content
- component-style
- navigation-presentation

These edits may be made during the call, but they are not considered accepted merely because the preview changed. The change must be persisted to governed Flutter source, tied to a Git diff/resulting revision, and re-run through Visual QA. Only then can the live session move to `client-confirmed`.

Material requests such as business rules, financial behavior, workflow/state changes, data, integrations, security/permissions or architecture are automatically classified as `material-change` and must route to a Change Contract. They cannot be applied as a minor Nowa edit.

Scope freeze rejects unfinished live-review sessions and material live requests without a Change Contract.
