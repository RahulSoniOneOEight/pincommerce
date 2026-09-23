# Design Governance, Promotion and Pattern Expansion

This layer closes the reusable-component governance loop.

## Lifecycle

Shared components move through candidate → evaluated → approved → deprecated. Every transition requires evidence; approval and deprecation also require an identified human approver.

## Promotion gate

Promotion requires:
- eligible dependency health
- review-ready or approved quality evidence
- passed rendered visual evidence
- affected-client review when shared changes have downstream impact
- explicit human approval

Learning scores can influence ranking but never satisfy a promotion gate.

## Design debt

CI generates machine-readable and Markdown design-debt artifacts from the existing debt scanner. Raw colors and mixed icon families remain visible as review work rather than silently becoming accepted conventions.

## Cross-platform parity

The expanded pattern manifest defines common state, action and data contracts for Flutter and web. CI requires symbols on both runtimes and non-empty behavioral contracts while still allowing platform-native presentation.

## Expanded shared patterns

The reusable runtime now adds:
- Filter Bar
- Checkout Summary
- Navigation Menu
- Form Section

These complement the original Product Card, Category Rail, B2B Quick Order, Dashboard KPI and Exception Table patterns.
