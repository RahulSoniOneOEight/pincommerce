# Design Runtime & Automated Quality

Stage 1 turns Design Intelligence selections into reusable Flutter and web runtime patterns.

## Implemented patterns

- Product Card
- Category Rail
- B2B Quick Order
- Dashboard KPI
- Exception Table
- Filter Bar
- Checkout Summary
- Navigation Menu
- Form Section

Each pattern is exposed through the shared `agency_flutter_ui` and `agency_web_ui` packages and represented in Widgetbook/Storybook with deterministic states.

## Quality evidence

`design-intelligence/runtime-quality.yaml` is the machine-readable Stage 1 contract. CI verifies:

- cross-platform pattern presence,
- catalog coverage,
- semantic/accessibility hooks,
- reduced-motion support on web,
- mobile/tablet/desktop capture targets,
- Flutter analyze/tests,
- Widgetbook analyze,
- Storybook production build.

The viewport contract defines 390px mobile, 768px tablet and 1440px desktop targets. CI now renders web screenshots and Flutter golden artifacts at these targets, records accessibility/performance evidence, and checks the web captures against the approved visual baseline authority.

## Governance

Product components consume shared theme/style roles rather than introducing page-local brand styling. Runtime components remain behind PinCommerce-owned wrappers so library choices can evolve without rewriting product surfaces.
