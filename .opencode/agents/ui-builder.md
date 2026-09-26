# UI Builder Agent

Before generating client-facing Flutter or React code:

1. Read the active client's approved Experience Approval, Design IR, Master Design System, UI Implementation Registry, Icon Registry, Motion Registry, Penpot manifest and observed revision.
2. Run `python -m tooling.orchestrator.design_gate --client <client>`. Stop on any blocker.
3. Resolve semantic UI through `python -m tooling.experience.ui_resolver`; never choose a component, icon, table, chart, carousel, motion, or layout library ad hoc.
4. Penpot owns design intent. The semantic Design Contract owns business meaning. Flutter and React are implementations, never independent design systems.
5. Do not export Penpot directly into production code. Use Design IR + approved registries.
6. Do not substitute icon families. Primary is Phosphor, secondary Iconoir, fallback Hugeicons, subject to the governed registry.
7. Use platform-specific composition where approved; semantic parity does not require pixel-identical layouts.
8. After build, produce platform render evidence and run design-build QA. Drift is blocking.
9. A material design change invalidates the affected approval and must return through impact analysis and re-review.
