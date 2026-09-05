# PinCommerce Design Control Plane

This repository is the versioned control plane for the PinCommerce Penpot design system and prototype definitions.

## Operating model

- **GitHub** stores the canonical design specification, tokens, component catalog, screen manifests, prototype routes, and sync code.
- **Penpot** is the live visual workspace.
- **Local Windows sync client** connects to Penpot's Remote MCP endpoint and acts on the file/page currently connected through Penpot's MCP plugin.
- Live writes are explicit, read-before-write, idempotent for managed state, and non-destructive in v1.

## Themes

- **Theme A — BuildKart Green:** retail-friendly teal/green direction.
- **Theme B — Premium Blue:** deep blue + white, restrained amber accent, and subtle watermark motifs at 2–4% opacity in selected premium surfaces only.

Both themes share one component hierarchy. Theme-specific component duplication is prohibited.

## Local Windows live Penpot flow

Prerequisites: Node.js 20+ and a Remote Penpot MCP key. In Penpot, open the intended target file and use **File → MCP Server → Connect** before running the commands below.

```powershell
git pull
npm install
Copy-Item .env.example .env
# edit .env and set PENPOT_MCP_URL to the full Remote MCP URL from Penpot
# optionally set PENPOT_FILE_ID to guard against writing to the wrong file
npm run penpot:check
npm run penpot:plan
npm run penpot:sync -- --apply
npm run penpot:verify
```

`penpot:check`, `penpot:plan`, and `penpot:verify` are read-only. `penpot:sync` refuses to write unless `--apply` is present. V1 never deletes Penpot content; unmanaged/orphaned content is reported and left untouched. Prototype links are reported unsupported if the currently exposed Penpot MCP/Plugin API cannot safely express them.

### Remote MCP implementation

The official Penpot Remote MCP exposes `execute_code`, which runs Penpot Plugin API JavaScript against the active connected file. The sync gateway discovers that capability at runtime. Managed identity is recorded in the current file's local library plugin data so repeated syncs can distinguish create/update/unchanged operations without relying only on human-readable names. Supported token-set operations also create/update real Penpot design tokens; component and screen operations create managed Penpot boards/components on the active page as the current bootstrap representation.

## Offline/control-plane commands

```bash
npm install
npm test -- --run
npm run typecheck
npm run validate
npm run sync:dry -- --out artifacts/penpot-plan.json
```

`npm run validate` loads and cross-validates all manifests. `npm run sync:dry` emits a deterministic operation plan and makes **no network calls** and **no Penpot writes**.

## Security

Never paste the MCP key into GitHub, commit `.env`, or include the full Remote MCP URL in issues/logs. `PENPOT_MCP_URL` is local-only. The client redacts common credential query parameters in connection errors. GitHub Actions does not run live Penpot commands and requires no Penpot secret.

## CI contract

Every pull request and push to `main` must pass dependency installation, tests, typecheck, manifest validation, and deterministic dry-run plan generation before merge.
