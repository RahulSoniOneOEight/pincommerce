# Penpot AI Kit Control Plane Design

## Objective

Move PinCommerce from a custom low-level visual renderer to a higher-level AI design workflow where GitHub remains the product/design control plane, Penpot AI Kit supplies design intelligence and workflow discipline, Penpot MCP executes against the live editable Penpot file, and Codex builds production application code from the approved design contract.

## Why change

The current live MCP foundation proved connectivity, guarded writes, managed identity and deterministic planning. The custom visual renderer also proved that Penpot can be manipulated programmatically, but it introduced avoidable complexity around geometry, component instances, workspace placement and visual-quality acceptance. The new architecture keeps the proven control-plane and MCP safety work while moving screen composition and design-quality iteration to Penpot AI Kit.

## Target architecture

User / Product Agent
→ PinCommerce GitHub control plane
→ Penpot AI Kit workflows
→ Penpot MCP
→ editable Penpot file
→ design-quality + accessibility checkpoints
→ approved DESIGN.md / tokens / component contract
→ Codex
→ React / Flutter / React Native
→ CI / production

## Responsibility split

### PinCommerce repository remains authoritative for

- product brief / PRD
- user journeys and screen inventory
- Theme A / Theme B brand constraints
- semantic token contract
- required component catalogue
- acceptance criteria
- design-agent brief templates and generated handoff bundles
- design run records and approval status
- live Penpot connectivity checks
- design contract validation in CI

### Penpot AI Kit becomes authoritative for design workflow behavior

Use the upstream kit rather than copying its implementation into this repo. The integration should reference/install the kit externally and generate PinCommerce-specific briefs compatible with its workflows.

Primary workflows/skills:
- `penpot-foundations`
- `penpot-component-factory`
- `penpot-build-screen`
- `brief-to-screen`
- `penpot-audit-accessibility`
- `penpot-audit-tokens`
- `penpot-design-md`
- `code-to-penpot-sync` where useful later

### Penpot MCP remains the live execution bridge

Retain the existing Remote MCP connectivity path and commands for target verification. Do not use the custom visual renderer as the default screen-generation engine.

### Codex becomes the application implementation agent

Codex consumes the approved design contract, exported/derived tokens, screen requirements and component inventory. Penpot-export is optional for structured CSS/SCSS/JSON token/style outputs, not the sole design-to-code contract.

## Control-plane files

Add a new `design-agent/` area:

- `design-agent/config.json` — workflow policy and required checkpoints
- `design-agent/briefs/b2c-home.md` — first production brief, based on the shared Make reference and Theme B
- `design-agent/briefs/_template.md` — reusable screen brief template
- `design-agent/runs/.gitkeep` — design-run records belong here when checked in
- `design-agent/README.md` — operator workflow

Add a small deterministic CLI under `agent/design-control/` that:

1. validates the design-agent config and briefs;
2. generates a self-contained handoff prompt/bundle for Penpot AI Kit;
3. records a stable run manifest without any MCP key or secret;
4. never writes directly to Penpot.

Proposed commands:

- `npm run design:validate`
- `npm run design:brief -- --screen b2c-home`
- `npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json`

The existing `penpot:check` remains the connectivity preflight. Existing custom renderer commands stay available for backwards compatibility but are documented as legacy/experimental and not the preferred generation path.

## B2C Home first production brief

Use the shared Make project as the visual/content reference but adapt it to the 390×844 mobile viewport and Theme B Premium Blue.

Required content:
- branded header
- search
- strong commerce hero inspired by the Make home
- category shortcuts
- Top Brands
- Flash Deals
- Top Rated Products
- bottom navigation

Design requirements:
- reusable existing tokens/components where available
- no hardcoded ad-hoc color system
- 4px spacing rhythm
- clear merchandising hierarchy
- editable Penpot-native output
- accessibility review
- design-quality review before approval

## Design run lifecycle

1. Product/control plane generates brief.
2. Operator opens target Penpot file and connects MCP.
3. AI assistant with Penpot AI Kit reads generated brief.
4. Kit preflights design system and proposes direction.
5. User approves direction.
6. Kit builds screen section-by-section.
7. Kit runs design-quality and accessibility review.
8. User visually approves or requests revisions.
9. Approved design is documented via DESIGN.md / design contract.
10. Codex implementation begins only from approved design state.

## Safety and governance

- No MCP key in repository, logs or run manifests.
- PinCommerce never vendors upstream Penpot AI Kit secrets/config.
- Meaningful canvas changes require user approval via the AI Kit workflow.
- Existing Penpot file should be duplicated for early trials if necessary.
- CI does not connect to live Penpot.
- CI validates briefs/config/run-manifest determinism only.
- Custom renderer remains non-default and may be retired later after successful AI Kit adoption.

## Acceptance criteria

Repository integration is complete when:

1. Design-agent config and brief template validate in CI.
2. `b2c-home` generates a complete Penpot AI Kit-compatible brief.
3. Generated handoff contains product context, viewport, Theme B constraints, required sections, reference guidance and quantitative acceptance criteria.
4. No secret or MCP URL is emitted.
5. A deterministic design run manifest can be produced twice with identical content for identical inputs.
6. README clearly documents the new preferred flow.
7. Existing Penpot live MCP preflight remains functional.
8. PR #3 custom renderer is explicitly marked superseded/experimental rather than merged as the primary design engine.

## Non-goals for this wave

- automating the upstream Penpot AI Kit installation inside CI
- committing a user MCP key
- direct background live writes from GitHub Actions
- production code generation from Penpot in the same wave
- full B2B redesign
- removing the custom renderer immediately

## Rollout

Wave 1: repository control-plane integration + B2C Home brief.
Wave 2: run B2C Home through Penpot AI Kit and visually approve it.
Wave 3: extend the same brief/run process to Category, Product, Cart and Checkout.
Wave 4: B2B screens, Theme A, DESIGN.md/Codex implementation loop.
