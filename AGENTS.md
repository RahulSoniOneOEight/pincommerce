# Agent Operating Contract

All AI/engineering agents must:
1. Read the active client project's `workflow/workflow-state.yaml` before acting.
2. Treat repository artifacts and contracts as authoritative; do not rely on chat memory for project state.
3. Read `.opencode/ai-routing.yaml` before selecting an AI role/provider.
4. Treat AI output as a proposal, never as project truth by itself.
5. Write AI proposals only under `client-projects/<client>/intelligence/ai/` and validate them before review.
6. Preserve separation between business capability, engineering domain, and provider.
7. Apply reuse-first resolution: existing client implementation → agency capability → approved component → approved OSS → extension → custom build.
8. Write material client feedback as a Change Contract before implementation.
9. Never self-authorize production release. Human production authorization is mandatory.
10. Do not change canonical entity ownership without updating the Data Contract and dependency map.
11. Keep integrations idempotent and auditable.
12. Add or update validation evidence for any changed contract, integration, critical journey, or AI-governance artifact.
13. Promote only the exact candidate validated in staging.
14. References inform; client objectives and governed truth decide. Every declared reference must end in REUSE, ADAPT, COMBINE, MODERNIZE, REJECT, or BUILD_NEW; silent non-use is forbidden.
15. A screen, YAML file, successful build, or agent assertion is not evidence of a completed journey. Completion requires the stage validator and required evidence.
16. Never change an approved upstream contract merely to make a downstream validator pass; invalidate and regenerate affected downstream artifacts instead.
17. Before designing or building, discover existing PinCommerce capabilities and classify them RETAIN, REUSE, ADAPT, UPGRADE, REPLACE, or BUILD.
18. Penpot/design components must be implementation-aware: semantic ID, tokens, states, responsive rules, Flutter/Web mapping, accessibility intent, and QA evidence are required before approval.
19. Builders do not approve their own work. Use independent design, journey, and runtime acceptance where the stage requires it.
20. Session/chat history is not project memory. Update workflow state, active decisions, CURRENT summary, checkpoint/handoff, and validation evidence at governed boundaries.
21. Client-facing UI code must resolve semantic components through the governed UI Implementation Registry; ad-hoc library selection is forbidden.
22. Penpot defines design intent; Design IR and semantic component contracts mediate implementation. Direct Penpot-to-production-code export is forbidden.
23. Icons resolve through the governed icon registry (Phosphor primary, Iconoir secondary, Hugeicons fallback unless an approved client registry overrides it); motion/layout/table/chart/carousel choices resolve through the UI registry.
24. Production UI generation requires the hard design gate and post-build design-build QA; drift from the approved Penpot/design revision is blocking.

## Model-role policy

- Strategy: ChatGPT preferred; DeepSeek fallback.
- Architecture: ChatGPT preferred; DeepSeek fallback.
- Implementation: DeepSeek preferred; ChatGPT fallback.
- Reviewer: ChatGPT preferred; DeepSeek fallback.

Provider choice is operational configuration, not business logic.
