# Marketplace / Mercur path from A through D

Mercur is a first-class marketplace provider that activates only when the client business model includes `marketplace`, `b2b-marketplace`, or `multi-vendor`.

## Phase A — client intelligence

Marketplace intake may capture seller onboarding/KYC, catalogue and inventory ownership, fulfilment/returns responsibility, commission model, settlement cycle, payout model, and dispute model under `marketplace_requirements`.

These requirements are copied into the governed Truth Register. The marketplace archetype contributes seller journeys, seller-portal surface requirements, and core marketplace capabilities.

## Phase B — solution intelligence

The marketplace archetype drives:
- Mercur selection behind the marketplace provider boundary
- seller, seller-offer, marketplace-order-allocation, commission, seller-settlement, and payout-reconciliation entities
- seller-onboarding-to-approval
- commerce-order-to-seller-allocation
- seller-settlement-to-accounting
- seller portal → marketplace runtime mapping

Medusa remains the commerce core and Tryton remains the ERP/accounting boundary where those domains are in scope.

## Phase C — functional marketplace prototype

When marketplace scope is active, Mercur is a required `real-core` module. Client review cannot become prototype-ready without Mercur health and seed evidence.

The deterministic Mercur seed now covers:
- sellers
- seller offers
- marketplace order allocations
- commission ledger
- seller settlements
- seller payout reconciliation

The standard rule remains: client-specific behavior is an overlay on the governed Mercur baseline.

## Phase D — productionization

Marketplace capabilities have explicit production ownership by the marketplace domain. The production compiler maps `seller-portal` to the marketplace runtime and resolves Mercur through its governed adapter/baseline.

Marketplace production migration adds:
- seller/offer/commission-rule migration
- opening seller settlement/payable migration and ERP reconciliation

The Phase-D acceptance model must not mark marketplace scope complete if marketplace capabilities are unmapped.

## Upstream source identity

The marketplace acceptance workflow verifies Mercur source commit:

`d73f28a85a22587778cf3e60db318b2628103a0d`

At that source identity the upstream monorepo declares Medusa 2.21.0 overrides and Bun 1.3.8.

This source-verification gate does not claim a live Mercur deployment. A live Mercur runtime, real seed import/read-back, seller-portal E2E, and Mercur→Tryton settlement reconciliation remain staging/runtime evidence tasks.
