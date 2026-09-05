# PinCommerce Design Control Plane

This repository is the versioned control plane for the PinCommerce Penpot design system and prototype definitions.

## Operating model

- **GitHub** stores the canonical design specification, tokens, component catalog, screen manifests, prototype routes, and sync code.
- **Penpot** is the live visual workspace.
- **Sync direction (phase 1):** GitHub → deterministic Penpot operation plan → Penpot adapter.
- The live Penpot transport is deliberately not assumed. A concrete adapter is added only after the deployment environment's actual Penpot MCP/API contract is confirmed.

## Themes

- **Theme A — BuildKart Green:** retail-friendly teal/green direction.
- **Theme B — Premium Blue:** deep blue + white, restrained amber accent, and subtle watermark motifs at 2–4% opacity in selected premium surfaces only.

Both themes share one component hierarchy. Theme-specific component duplication is prohibited.

## Commands

```bash
npm ci
npm test -- --run
npm run typecheck
npm run validate
npm run sync:dry -- --out artifacts/penpot-plan.json
```

`npm run validate` loads and cross-validates all manifests. `npm run sync:dry` emits a deterministic operation plan and makes **no network calls** and **no Penpot writes**.

## Security

Never commit OpenAI, GitHub, or Penpot credentials. Use local environment variables or CI secrets. `.env.example` contains names only.

## CI contract

Every pull request and push to `main` must pass dependency installation, tests, typecheck, manifest validation, and deterministic dry-run plan generation before merge.
