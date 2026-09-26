# Phase 1 — Complete Intelligent Build Contract

Phase 1 turns client truth and declared references into a journey-complete, implementation-aware and runtime-validated prototype. Existing PinCommerce runtimes remain authoritative; this layer orchestrates and validates them rather than replacing them.

## Automated path

1. Capability discovery classifies existing platform capability before new build.
2. Detailed Journey Graph makes actions, states, permissions, events and transitions explicit.
3. Reference adaptation records an explicit decision for every declared source.
4. Journey capability mapping connects experience actions to platform domains/runtimes and emits implementation gaps.
5. Experience strategy prioritizes journeys and assigns each surface a role.
6. Component Contract Registry maps semantic components to Flutter and Web implementations, states, tokens, accessibility and QA.
7. Design IR is the implementation-neutral bridge from journey nodes to platform components.
8. Multi-surface builders consume the Design IR and domain contracts; provider engines stay behind adapters.
9. Core runtime acceptance requires real Medusa/Mercur/Tryton evidence where those runtimes are required. External providers may use approved mocks/sandboxes during prototype.
10. Independent design, journey and runtime critics must pass.
11. Integrated readiness requires the seven Phase-1 vertical slices and all critics.
12. Client review remains a human gate.

## Status semantics

experience-prototype-complete means the design/journey contract is coherent. It does not mean backend integration is complete.

integrated-runtime-ready means required core runtimes have health and seed evidence.

integrated-prototype-ready requires both plus browse-to-buy, payment failure recovery, order-to-ERP, order-to-shipment, return/refund, seller settlement and reconciliation evidence.

## Commands

Generate journey/reference/capability intelligence:

    python -m tooling.intelligence.phase1 --client <client> --overwrite

Generate strategy, component contracts, Design IR and critic/readiness evidence:

    python -m tooling.orchestrator.phase1_build --client <client> --overwrite

Re-check integrated readiness without changing artifacts:

    python -m tooling.orchestrator.phase1_build --client <client> --check

The readiness command intentionally blocks if real required core runtime evidence is absent. A screen, YAML file, build success or agent assertion cannot substitute for runtime evidence.

## Human authority

Experience approval and client review remain explicit human gates. Phase 1 automation may propose and generate artifacts but cannot self-approve those gates.
