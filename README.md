# PinCommerce Design Control Plane

This repository is the versioned control plane for the PinCommerce Penpot design system and prototype definitions.

## Operating model

- **GitHub** stores the canonical design specification, tokens, component catalog, screen manifests, visual renderer manifests, prototype routes, and sync code.
- **Penpot** is the live visual workspace.
- **Local Windows sync client** connects to Penpot's Remote MCP endpoint and acts on the file/page currently connected through Penpot's MCP plugin.
- Live writes are explicit, read-before-write, idempotent for managed state, and non-destructive in v1.

## Themes

- **Theme A — BuildKart Green:** retail-friendly teal/green direction.
- **Theme B — Premium Blue:** deep blue + white, restrained amber accent, and subtle watermark motifs at 2–4% opacity in selected premium surfaces only.

Both themes share one component hierarchy. Theme-specific component duplication is prohibited.

## Visual Renderer v1

The first visual-renderer wave upgrades the managed Penpot scaffolding into native editable Theme B UI for the core reusable commerce components plus B2C **Home**, **Category**, and **Product** screens.

The renderer uses a hybrid offline asset strategy:

- category imagery is drawn from deterministic editable Penpot-native geometry;
- product media uses deterministic neutral placeholders that can later be replaced by real product assets;
- no stock-photo or network image dependency is required;
- prototype links remain intentionally unsupported in this wave.

Visual children are owned only when their names begin with `PCV1::<repoId>::`. Re-rendering reconciles that owned subtree while leaving unrelated user-created Penpot content untouched. A visual fingerprint is stored alongside the existing managed registry entry so repeated identical syncs produce zero visual updates.

## Local Windows live Penpot flow

Prerequisites: Node.js 20+ and a Remote Penpot MCP key. In Penpot, open the intended target file and use **File → MCP Server → Connect** before running the commands below.

```cmd
git checkout feat/penpot-visual-renderer-v1
git pull
npm install
npm run penpot:check
npm run penpot:plan
npm run penpot:sync -- --apply
npm run penpot:verify
npm run penpot:plan
```

While PR #3 is under review, use the feature branch above. After merge, use `main` instead.

Before the first visual apply on an already structurally synced Penpot file, `penpot:plan` should report `create:0` and updates only for the visual targets whose fingerprints are absent or stale. After a successful apply, the final `penpot:plan` should report `create:0` and `update:0` for supported objects.

`penpot:check`, `penpot:plan`, and `penpot:verify` are read-only. `penpot:sync` refuses to write unless `--apply` is present. V1 never deletes managed roots or unrelated Penpot content; unmanaged/orphaned content is reported and left untouched. Prototype links are reported unsupported if the currently exposed Penpot MCP/Plugin API cannot safely express them.

### Remote MCP implementation

The official Penpot Remote MCP exposes `execute_code`, which runs Penpot Plugin API JavaScript against the active connected file. The sync gateway discovers that capability at runtime. Managed identity is recorded in the current file's local library plugin data so repeated syncs can distinguish create/update/unchanged operations without relying only on human-readable names. Supported token-set operations create/update real Penpot design tokens; the visual renderer now enriches existing managed component and screen roots with editable native shapes.

## Offline/control-plane commands

```bash
npm install
npm test -- --run
npm run typecheck
npm run validate
npm run sync:dry -- --out artifacts/penpot-plan.json
```

`npm run validate` loads and cross-validates the structural manifests. The live commands additionally validate the visual renderer manifests before planning or applying visual updates. `npm run sync:dry` emits the deterministic structural operation plan and makes **no network calls** and **no Penpot writes**.

## Security

Never paste the MCP key into GitHub, commit `.env`, or include the full Remote MCP URL in issues/logs. `PENPOT_MCP_URL` is local-only. The client redacts common credential query parameters in connection errors. GitHub Actions does not run live Penpot commands and requires no Penpot secret.

## CI contract

Every pull request and push to `main` must pass dependency installation, tests, typecheck, manifest validation, and deterministic dry-run plan generation before merge.
