# Design Intelligence Stage 2

Stage 2 connects the governed design runtime to external design evidence, dependency-health evidence and production learning without allowing those signals to silently alter an approved client design.

## Design-source ingestion

`tooling.experience.source_ingestion` supports Figma, Penpot, Git, reference sites, brand guides and client media. Figma/Penpot provider-shaped payloads are normalized directly. Every normalized source carries a source ID/type, capture timestamp, deterministic SHA-256 content hash and optional provider reference.

`merge_inventory` rejects duplicate or unprovenanced records. Provider authentication and network collection remain outside the deterministic acceptance core; collected API/export payloads enter through the same provenance boundary.

## Dependency intelligence

`tooling.experience.dependency_intelligence` evaluates dependency snapshots independently of visual preference. It checks license policy, release age, vulnerability severity and runtime/version/framework compatibility evidence. Results are `eligible`, `review` or `blocked`.

A blocked dependency cannot win a visual benchmark or be promoted into the runtime. Snapshot evaluation keeps CI reproducible while separate collectors can refresh current release, license and security evidence.

## Learning loop

`tooling.experience.learning_loop` combines design-review outcomes and UX telemetry into bounded advisory ranking adjustments. Signals require a minimum observation count, are capped, never auto-promote a component, never mutate an approved client design and always preserve human approval.

## Flow

```text
Figma / Penpot / Git / reference / brand / client media
→ provenance + normalization
→ source inventory
→ dependency snapshots
→ license + maintenance + security + compatibility eligibility
→ governed selection / benchmark
→ production outcome + UX telemetry
→ bounded advisory learning signal
→ next-client ranking input
→ human approval
```

## Acceptance

```bash
python -m unittest tests.test_design_learning_stage2 -v
```
