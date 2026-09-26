# Current Project Context — reference-retail

This file is the compact restart context for OpenCode. Governed contracts and workflow state remain authoritative.

- Client: reference-retail
- Canonical workflow state: read `../workflow/workflow-state.yaml`
- Phase-1 policy: discover/reuse existing capabilities before new implementation
- Core runtime intent: Medusa commerce, Mercur marketplace where required, Tryton ERP, NATS/event integration
- Human authority: experience/scope, UAT and production authorization remain explicit gates
- Resume rule: validate canonical workflow state first; then load only the active phase contracts and evidence
- Do not: infer current truth from historical chat/session logs
