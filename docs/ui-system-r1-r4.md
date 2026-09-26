# PinCommerce UI System R1-R4

This implementation binds the shared design/build system into the existing Steps 20-54 lifecycle.

## R1 — Design Contract Foundation (P1-P4)
- Master Design System and semantic tokens
- Semantic component contracts and platform implementation registry
- Phosphor primary / Iconoir secondary / Hugeicons fallback icon policy
- Motion registry with Flutter/Web runtime mapping
- Deterministic UI resolver

## R2 — Penpot Design Automation (P5-P7)
- Semantic Penpot operations generated from Master Design System, Design IR, journey graph and implementation registry
- Real write execution supported through a configured authenticated Penpot bridge endpoint (`PENPOT_WRITE_URL`)
- Exact project/revision evidence required
- Responsive breakpoints, states, components and interactive journeys included in the operation payload

The repository does not invent Penpot revisions. CI can validate payload generation; live Penpot writes require an authorized bridge endpoint and token.

## R3 — Governance & Human Review (P8-P10)
- Existing Review Mode V2 remains the consolidated human review surface
- Existing critics/change loop/re-QA remain authoritative
- Experience freeze now binds Master Design System, implementation, icon and motion registries plus Penpot observed revision

## R4 — Runtime Mapping & Drift Prevention (P11-P14)
- Platform implementation registry maps semantic components to owned Flutter/Web components and specialist libraries
- OpenCode UI Builder instructions prohibit ad-hoc library selection
- Design-build QA requires deterministic mapping plus rendered platform evidence
- Build gate blocks stale or incomplete design authority

## Specialist defaults
- Icons: Phosphor → Iconoir → Hugeicons
- Motion: Flutter `flutter_animate`; Web Motion; rich animation Rive/Lottie
- Carousel: Flutter PageView/carousel_slider; Web Embla
- Tables: Flutter data_table_2; Web TanStack Table
- Charts: Flutter fl_chart; Web Recharts
- Layout: Flutter GridView/staggered grid; Web CSS Grid/Tailwind

These are implementation defaults, not business truth. Client-approved contracts can override them only through governed registry changes.
