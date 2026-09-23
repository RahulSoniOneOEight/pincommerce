# Reference Marketplace Runtime Acceptance

The `reference-marketplace` client proves that the marketplace path is conditional, governed, and executable without changing the normal retail path.

## Scope

The committed client input activates both `marketplace` and `multi-vendor`, including seller onboarding, seller catalogue/offers, seller inventory, marketplace order allocation, commission rules, settlements, seller analytics, seller approval and payout reconciliation.

The deterministic acceptance runner validates:

- **A** — marketplace classification, benchmark and Truth Register coverage
- **B** — Mercur selection, marketplace entities and cross-domain dependencies
- **C** — Mercur is mandatory `real-core` for marketplace scope and the governed seed covers the seller lifecycle
- **D** — marketplace capability ownership, seller-portal runtime mapping and marketplace migration steps

## Live runtime proof

CI checks out upstream Mercur at:

`d73f28a85a22587778cf3e60db318b2628103a0d`

It installs the upstream basic template, runs real Mercur/Medusa migrations against PostgreSQL, executes Mercur's application seed, starts the backend and verifies `/health`.

The job then reads the seeded marketplace state back from PostgreSQL and requires:
- at least three sellers
- at least one marketplace offer
- the canonical upstream demo seller
- live `seller`, `offer` and `commission_line` schema presence

The governed PinCommerce marketplace seed is separately validated for sellers, offers, allocations, commission ledger, seller settlements and payout reconciliation, and mapped against the live Mercur marketplace schema.

## ERP boundary

The same workflow boots Tryton 8.0 and checks the deterministic seller settlement reconciliation contract:

`Mercur settlement payable == ERP seller payable == payout reconciliation amount`.

This proves the governed accounting boundary and a live Tryton runtime. It does not claim that the deterministic seller payable was posted into Tryton through a production API.

## Remaining environment boundary

Real payment/logistics/WhatsApp credentials, production seller KYC, live payout execution and production deployment remain Phase-E staging/release responsibilities.
