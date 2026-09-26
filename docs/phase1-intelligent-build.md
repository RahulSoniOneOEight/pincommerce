# Phase 1 — Intelligent Design, Build & Integrated Prototype

Phase 1 extends the existing PinCommerce lifecycle; it does not replace working Medusa, Mercur, Tryton, NATS, provider adapters, release governance, or existing contracts.

## Core rule

Before design or implementation, discover existing capabilities and classify them as RETAIN, REUSE, ADAPT, UPGRADE, REPLACE, or BUILD. New work is justified only by a real capability, journey, design, or runtime gap.

## Runtime/UX boundary

- Customer app/storefront -> Commerce domain contract -> Medusa
- Seller portal/admin -> Marketplace domain contract -> Mercur
- PinCommerce ERP/Accounting UX -> ERP domain contract -> Tryton adapter -> Tryton
- Domain services -> canonical events -> NATS JetStream
- Payment/logistics/messaging -> provider-neutral connector contracts
- Commerce Admin may compose cross-domain read models from commerce, marketplace, payment, logistics, ERP and reconciliation.

The UX must never be designed as though a provider UI is the PinCommerce experience.

## Phase flow

Client truth + existing platform
-> capability discovery/registry
-> detailed journeys
-> reference intelligence
-> domain capability intelligence
-> implementation gap
-> experience strategy
-> implementation-aware Penpot/design contracts
-> Flutter/Web/Admin/ERP build
-> real Medusa/Mercur/NATS/Tryton core integration
-> Design Critic + Journey Critic + Runtime Critic
-> auto-fix/retest
-> integrated-prototype-ready
-> human client review.

## Prototype meanings

**experience-prototype-complete** means required surfaces, screens, components, states and rendered visual evidence are complete.

**integrated-prototype-ready** additionally requires real core runtime evidence and passing vertical slices for browse-to-buy, payment recovery, order-to-ERP, order-to-shipment, return/refund, seller settlement and reconciliation.

External providers may use sandbox/mock implementations where the contract allows it. Core runtimes required by the solution contract may not be replaced by UI-only mocks.

## Session continuity

A new OpenCode session must reconstruct state from the repository. The target client workspace includes:

- workflow/workflow-state.yaml
- context/CURRENT.md
- context/decisions.yaml
- context/handoff.yaml
- sessions/*.yaml and *.md

Historical session logs explain what happened; current contracts, active decisions and workflow state define current truth.

## Compatibility

The existing workflows/lifecycle.yaml remains the business lifecycle. workflows/phase1-intelligent-build.yaml is an execution-control contract underneath it. Existing tooling/workflow/runtime.py remains authoritative for canonical lifecycle state until explicit mappings are added and validated.
