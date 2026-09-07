# PinCommerce Design Control Plane

This repository is the versioned product/design control plane for PinCommerce. **Penpot AI Kit + Penpot MCP is the preferred screen-design path**; GitHub remains authoritative for product briefs, journeys, theme constraints, component requirements, acceptance criteria and run records.

## Preferred AI app-builder flow

```text
Product idea / PRD
→ PinCommerce design contract in GitHub
→ Penpot AI Kit workflow
→ Penpot MCP
→ editable Penpot design
→ design-quality + accessibility review
→ visual approval
→ DESIGN.md / tokens / component contract
→ Codex
→ React / Flutter / React Native
```

For the first production screen:

```cmd
npm install
npm run design:validate
npm run design:brief -- --screen b2c-home
npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json
npm run penpot:check
```

Then provide the generated handoff to an MCP-capable assistant with the upstream `penpot/penpot-ai-kit` installed/configured while the intended Penpot file is open and connected. See `design-agent/README.md`.

## Operating model

- **GitHub / PinCommerce** stores the canonical product brief, design specification, Theme A/Theme B constraints, component catalog, screen inventory, acceptance criteria and design-run metadata.
- **Penpot AI Kit** supplies the preferred design workflow behavior: foundations/components where needed, screen building, design-quality review, accessibility review and design documentation.
- **Penpot MCP** is the live AI ↔ canvas bridge against the active connected file.
- **Penpot** is the editable visual system of record.
- **Codex** is the downstream application implementation agent after design approval.
- The existing direct custom visual renderer/sync path is retained for experimentation and backwards compatibility; it is **not the preferred screen-design engine**.

## Themes

- **Theme A — BuildKart Green:** retail-friendly teal/green direction.
- **Theme B — Premium Blue:** deep blue + white, restrained amber accent, and subtle watermark motifs at 2–4% opacity in selected premium surfaces only.

Both themes share one component hierarchy. Theme-specific component duplication is prohibited.

## Local Windows live Penpot preflight / experimental sync

Prerequisites: Node.js 20+ and a Remote Penpot MCP key. In Penpot, open the intended target file and use **File → MCP Server → Connect** before running live commands.

```powershell
git pull
npm install
Copy-Item .env.example .env
# edit .env and set PENPOT_MCP_URL to the full Remote MCP URL from Penpot
# optionally set PENPOT_FILE_ID to guard against writing to the wrong file
npm run penpot:check
```

`penpot:check` is the preferred read-only target preflight before an AI Kit design session.

The older direct renderer/sync commands remain available for controlled experiments:

```powershell
npm run penpot:plan
npm run penpot:sync -- --apply
npm run penpot:verify
```

`penpot:check`, `penpot:plan`, and `penpot:verify` are read-only. `penpot:sync` refuses to write unless `--apply` is present. The direct renderer/sync path remains non-destructive in v1 and should not be used as the default screen-composition workflow.

### Remote MCP implementation

The Penpot Remote MCP exposes an `execute_code` capability that can act against the active connected file through the Penpot Plugin API. The existing PinCommerce gateway discovers this capability at runtime and retains managed identity/target safety for experimental direct sync. The preferred AI Kit flow uses MCP as the execution bridge while delegating design composition and quality iteration to the upstream kit.

## Offline/control-plane commands

```bash
npm install
npm test -- --run
npm run typecheck
npm run validate
npm run design:validate
npm run design:brief -- --screen b2c-home
npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json
npm run sync:dry -- --out artifacts/penpot-plan.json
```

`design:validate`, `design:brief` and `design:run-manifest` are offline and make no Penpot writes. The generated design manifest is deterministic for identical inputs. `npm run sync:dry` remains the existing structural dry-run and also makes no network calls or live writes.

## Security

Never paste the MCP key into GitHub, commit `.env`, or include the full Remote MCP URL in issues, briefs, manifests or logs. `PENPOT_MCP_URL` is local-only. GitHub Actions does not run live Penpot commands and requires no Penpot secret.

## CI contract

Every pull request and push to `main` must pass dependency installation, tests, typecheck, structural manifest validation, **design-agent contract validation**, deterministic design-run generation and deterministic Penpot dry-run plan generation before merge.
