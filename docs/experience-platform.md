# Experience Platform

Part 3A converts governed solution artifacts into reviewable multi-surface experience directions.

## Inputs

- capability-map.yaml
- journey-map.yaml
- surface-map.yaml
- Design Contract (partial: presence-checked, not yet schema-validated)
- approved AI/strategy proposals where relevant (advisory; see `docs/governance-status.md`)

## Generated outputs

- Direction A: discovery-first
- Direction B: search-first
- Direction C: task-first
- deterministic fixture set
- prototype manifests per direction

## Rules

Directions must differ materially in:
- navigation
- discovery
- task priority
- interaction model
- information density

They must not be simple color/theme variants.

## Commands

Preview:
`python -m tooling.experience.generator --client reference-retail --print-only`

Generate:
`python -m tooling.experience.generator --client <client-id>`

Regenerate intentionally:
`python -m tooling.experience.generator --client <client-id> --overwrite`

## Review pipeline

Direction → Prototype Build → Visual QA → Review Session → Client/Internal Review → Nowa live minor refinement when requested → post-change Git/Visual QA → client confirmation → Selection/Mix-and-Match → Change Contract where needed.

## Tooling

Flutter:
- agency_flutter_ui
- Widgetbook
- Golden Tests
- Nowa live client-review refinement for minor Flutter visual/UX changes

Web:
- agency_web_ui
- React / Next.js
- Storybook
- browser visual regression

OpenCode orchestrates the flow. ChatGPT is preferred for experience strategy/review; DeepSeek is preferred for implementation scaffolding and repetitive fixture/component generation.


## Nowa live client-review role

Nowa is the governed live-edit environment for Flutter during client review calls. It is not a parallel source of truth.

Allowed live categories:
- spacing
- layout
- typography
- content/copy
- component styling
- navigation presentation

Material categories are not edited live as minor changes:
- business rules
- financial logic
- state machines/workflows
- data ownership
- integrations
- security/permissions
- architecture

Every live call is represented by a `Live Client Review Session` artifact. Minor edits may be applied in Nowa only when they are recorded with target, before/after intent, affected Git paths, Git diff reference and resulting source revision. The resulting revision must return through Visual QA before the client can confirm the change. Material requests route to a Change Contract.

Nowa therefore sits inside the governed review loop:

```text
Review Session
→ Nowa live call
→ classify request
   ├─ minor visual/UX → apply → persist to Flutter source → Git diff → Visual QA
   └─ material change → Change Contract
→ client confirmation
→ scope freeze
```
