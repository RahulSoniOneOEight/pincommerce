# PinCommerce — Agency Platform V2

PinCommerce is the reference implementation of the Agency Platform V2 operating model: governed client onboarding, industry/archetype benchmarking, capability and journey intelligence, reusable solution composition, multi-surface delivery, contract-driven production, QA, release, and operations.

## Core principles

- Client request is not the implementation specification.
- Benchmark against industry/archetype best practice before scope is frozen.
- Reuse existing platform capability and approved OSS before custom building.
- Separate business capabilities from engineering domains and providers.
- Agents coordinate through repository artifacts and contracts, not chat memory.
- Human approval is required for material business, security, financial, UAT, and production decisions.
- Promote the exact candidate validated in staging.

## Platform layers

1. Client Truth and Onboarding
2. Industry / Archetype Intelligence
3. Capability / Journey / Entity / Surface / Dependency Intelligence
4. Solution Architecture and Provider Selection
5. Experience Directions and Multi-Surface Prototype
6. Review, Visual QA, and Change Contracts
7. Production Contracts and Domain Implementation
8. Integration, Automation, Data, and Analytics
9. Cross-Domain QA, UAT, Release, and Operations

See `docs/architecture.md` and `docs/client-delivery.md` for the operating model.

## Pre-production completion

The authoritative completion gate for the governed flow from client onboarding through immutable
scope freeze (points 1–40) is:

```bash
python -m tooling.validation.preproduction --client <client> --check-drift
```

See `docs/preproduction-completion.md` for the evidence model and boundary.
