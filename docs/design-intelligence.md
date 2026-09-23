# Design Intelligence and UI Selection

PinCommerce UI/UX selection is evaluation-driven. Agents do not choose a component library, screen pattern, icon set, motion library, theme or palette from preference alone.

## Inputs

The design evaluator consumes:
- business model and target surfaces
- required journeys and experience requirements
- existing client app/web systems
- reusable Git code/components
- Figma/Penpot references
- brand guides and brand colors
- reference websites
- client media
- approved PinCommerce components and patterns
- the curated open-source reference pool

These are recorded in `experience/design/source-inventory.yaml`.

## Reuse and selection order

For each UI requirement:
1. existing client component
2. existing PinCommerce component
3. approved PinCommerce pattern
4. approved open-source candidate
5. configure/extend an existing component
6. custom governed component

A large reference pool is allowed for intelligence, but the runtime dependency pool remains deliberately small. Every selected OSS dependency must sit behind PinCommerce shared primitives unless an exception is explicitly approved.

## Active production candidate pool

Flutter defaults to `shadcn_flutter` behind `agency_flutter_ui`, with Material/Cupertino interoperability. Specialist candidates include `data_table_2`, `flutter_form_builder`, `fl_chart`, `cached_network_image`, and `carousel_slider`. Icon candidates are Iconoir, Phosphor, Lucide and Material Symbols; Iconoir is the default. Motion candidates are `flutter_animate`, native Flutter animation, Rive and Lottie.

Web defaults to PinCommerce-owned shadcn/ui compositions over Base UI where suitable, with Radix/React Aria compatibility. Specialist candidates include TanStack Table, TanStack Query, React Hook Form, Recharts and Embla. Icon candidates are Iconoir, Lucide, Phosphor and Material Symbols; Iconoir is the default. Motion defaults to Motion for React, with CSS/WAAPI for simple transitions and GSAP only for justified advanced timelines/scrollytelling.

Ant Design, MUI, Moon Design, base_ui_flutter, ERP-oriented systems and the broader reference catalogue remain available for evaluation when the surface warrants them; they are not global defaults.

## Functional pattern selection

The registry maps function to candidate components. Examples:
- product/card discovery → image-aware shared cards + Iconoir + restrained motion
- category rails → carousel/Embla
- B2B quick order → DataTable2/TanStack Table + form primitives
- seller settlement/reconciliation → dense table + analytical chart
- checkout/onboarding/KYC → Form Builder/React Hook Form
- dashboard KPIs → fl_chart/Recharts
- exception operations → dense tables and status patterns

The output is `experience/design/selection.yaml`, including the candidate pool, selected stack and decision reasons.

## Theme and token resolution

Production UI consumes semantic roles, never arbitrary component-local brand hex values. The flow is:

`client raw brand values → semantic role resolution → PinCommerce visual preset → direction override → runtime binding`

Initial presets:
- `premium-modern`
- `compact-commerce`
- `editorial-commerce`

Direction A/B/C may override the base preset while sharing the same semantic token contract.

## Motion policy

Motion is classified into micro-feedback, UI transitions, card/state changes, page transitions and hero/story motion. Reduced-motion support is mandatory. Decorative motion is discouraged on dense operational surfaces, and GSAP requires an advanced-timeline justification.

## Imagery and Pexels

Image/media sourcing follows:
`client-supplied → existing project assets → PinCommerce approved fixtures → Pexels → neutral placeholder`.

Pexels is the approved external fallback for missing hero/editorial/lifestyle/category imagery. `tooling.experience.pexels_assets` uses `PEXELS_API_KEY`, requests multiple candidates and records provider asset ID, source page, photographer and image metadata. The final image is still subject to visual QA.

## Best-of-component quality gate

A component or composition cannot become approved reusable UI based only on an AI visual opinion. The quality gate combines:
- functional fit
- visual quality
- information hierarchy
- interaction quality
- responsive fit
- accessibility
- brand alignment
- performance
- reusability

The default threshold is 80/100, with deterministic evidence required. High-value screens can run an A/B/C tournament; only eligible candidates enter the tournament and the highest evidence-backed score becomes the review winner. Human review remains part of approval.

## Flow

```text
Client requirements + brand/assets + Git/Figma/Penpot/reference sites
→ source inventory
→ classify experience and surface type
→ reuse evaluation
→ pattern requirements
→ approved component/source pool
→ component/icon/motion selection
→ visual preset selection
→ semantic token resolution
→ asset resolution (Pexels only if needed)
→ compose A/B/C directions
→ screenshot/golden/functional/accessibility QA
→ evidence-backed quality score
→ client review
→ approved reusable component/theme
```

## Advanced implementation and learning loop

The governed selection layer is followed by an implementation compiler and evidence gates.

```text
selection.yaml
→ Design Implementation Compiler
→ dependency candidates + PinCommerce wrapper plan
→ Widgetbook / Storybook catalog targets
→ required component states
→ semantic icon + motion token bindings
→ accessibility + performance + state-completeness gates
→ equal-fixture component benchmark
→ screenshot / golden evidence
→ Visual QA + quality tournament
→ candidate / approved component lifecycle
→ production UX outcomes
→ future candidate-ranking input
```

### Implementation compiler

`python -m tooling.experience.implementation_compiler --client <client-id>`

The compiler converts the selected stack into a platform implementation plan. It identifies shared-package targets, dependency candidates, PinCommerce wrapper names, catalog targets, required states and blocking quality gates. It does not silently install a dependency before license/maintenance/security eligibility is proven.

### Component metadata and dependency health

`design-intelligence/component-metadata.yaml` records functional/design characteristics. Dependency eligibility is evaluated separately from visual preference. A stale, blocked-license or blocked-security component cannot be promoted merely because it looks better.

### Equal-fixture benchmark

`python -m tooling.experience.benchmark --client <client-id>`

Candidate components are compared using the same fixture, semantic theme, content, viewport and state. Standard benchmark viewports are mobile 390, tablet 768 and desktop 1440. This is the basis for automated screenshot/golden tournaments.

### Deterministic implementation gates

Reusable components must prove:
- required state completeness
- semantic token usage
- semantic icon usage
- keyboard/focus/semantics/contrast/reduced-motion accessibility
- performance budget
- responsive behavior
- cross-platform behavioral parity where both Flutter and web variants exist
- visual QA and quality threshold

### Source ingestion

`tooling.experience.source_import` normalizes exported Figma, Penpot, Git component inventory, reference-site analysis and brand-guide metadata into the same design-intelligence shape. Network/provider-specific extraction remains outside the deterministic core; exported evidence is normalized before it can influence governed selection.

### Theme compiler

`tooling.experience.theme_compiler` creates light/dark semantic variants and contrast evidence. Client raw colors remain inputs, not direct component values.

### Design debt and change impact

`tooling.experience.design_debt` detects raw color usage and mixed icon families. `tooling.experience.impact` identifies all client selections affected by a shared pattern change before promotion.

### Production feedback

Design outcomes and production UX telemetry may influence future candidate ranking but cannot silently alter an approved client design. Accepted/rejected outcomes and metrics are advisory learning evidence subject to the next client's own requirements and human approval.
