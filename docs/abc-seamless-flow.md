# A/B/C Seamless Flow and End-C Handoff

## A — Client and market intelligence

Inputs:
- client brief and source references
- business model, goals, constraints, integrations
- explicit UX requirements
- explicit Medusa/Mercur/Tryton overrides

Outputs:
- Client Truth Register
- normalized Client Profile
- industry/archetype classification evidence
- benchmark report
- capability gap + prioritized impact analysis

A is ready only when unresolved assumptions, unknowns and conflicts are cleared before final scope freeze.

## B — Solution intelligence

Outputs:
- reuse decisions
- Capability Map
- Journey Map
- Entity Map
- Surface Map
- Integration Map
- Dependency Map
- Solution Contract
- accepted Architecture Decisions

A generated provider choice remains proposed until the relevant ADR is explicitly accepted.

## C — Functional prototype and client approval

The functional prototype consists of:
- complete required UI surfaces
- implementation evidence for required screens/components/states
- real Medusa/Mercur/Tryton core runtimes where applicable
- linked deterministic master/transaction/finance demo data
- seeded provider runtimes
- ready mock/sandbox external providers
- immutable build identity
- capture manifest
- Visual + Business QA
- Review Session
- immutable Prototype Revision
- explicit Review Round
- structured text Review Feedback
- governed Nowa live-review sessions
- Change Contracts for material changes

Client review cannot begin until the UI and functional-core gates pass.

The client-review loop is explicit:

`Prototype Revision 001 → Review Round 001 → feedback/changes → Prototype Revision 002 → Review Round 002 → ... → final approved round`

Review feedback may be entered as plain client text, but is stored with surface/journey/screen/component context and deterministic classification/routing.

Scope freeze additionally requires:
- A truth is resolved
- all active ADRs are accepted
- all required surfaces are approved
- all required journeys are approved
- every required surface has passing QA
- every mandatory Visual QA check is present and passed
- only live-review sessions attached to the selected Review Session are considered
- the reviewed coverage/runtime references are still current

## End of C: authoritative handoff

The primary authority is the mutable pointer:

`approved/current-scope.yaml`

It points to one immutable versioned baseline:

`approved/scope-baselines/BASE-<client>-vN.yaml`

The historical `approved/scope-baseline.yaml` is retained only for backward compatibility on projects created before versioned baselines.

A newly generated baseline records:
- truth register reference
- Solution Contract
- selected Experience Direction
- prototype coverage
- prototype implementation evidence
- functional core runtime reference
- linked demo dataset
- immutable build ID
- approved Review Session
- passing Visual QA records
- approved surfaces
- approved journeys
- accepted Architecture Decisions
- attached live-review sessions
- included/excluded/deferred capabilities
- final Prototype Revision reference
- final Review Round reference
- client approver and approval timestamp

Supporting evidence remains in:
- `derived/`
- `solution/`
- `experience/directions/`
- `experience/prototypes/`
- `experience/fixtures/`
- `experience/builds/`
- `experience/visual-qa/`
- `feedback/`
- `changes/`

The baseline referenced by `approved/current-scope.yaml` is the single production handoff authority into stage 20: Production Contracts. Older versioned baselines remain immutable audit history.
