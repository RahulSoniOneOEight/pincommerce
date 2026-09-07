# PinCommerce Design Agent

This directory is the PinCommerce product/design contract for the preferred **Penpot AI Kit + Penpot MCP** workflow. It does not contain the upstream AI Kit implementation and it never stores MCP credentials.

## Preferred flow

1. Validate the repository design contract.
2. Generate a screen-specific handoff for Penpot AI Kit.
3. Generate a deterministic design-run manifest for audit/versioning.
4. Open the intended Penpot file and connect **File → MCP Server → Connect**.
5. Run the existing read-only Penpot target preflight.
6. Give the generated handoff to an MCP-capable assistant with the upstream `penpot/penpot-ai-kit` installed/configured.
7. Approve the proposed direction before meaningful canvas changes.
8. Review the screen after design-quality and accessibility checks.
9. Only after visual approval, produce DESIGN.md/tokens/component handoff for Codex application implementation.

## Windows Command Prompt

```cmd
cd /d C:\Users\LENOVO\pincommerce
git pull
npm install
npm run design:validate
npm run design:brief -- --screen b2c-home
npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json
npm run penpot:check
```

`design:brief` prints the self-contained Penpot AI Kit handoff to the terminal. It does not modify Penpot. `design:run-manifest` records only stable, non-secret input fingerprints and workflow metadata.

## Files

- `config.json` — workflow provider, checkpoints, themes and viewport defaults.
- `briefs/_template.md` — reusable PinCommerce screen-brief structure.
- `briefs/b2c-home.md` — first production brief, based on the shared Make reference and Theme B.
- `runs/` — optional checked-in design-run/approval records; never put credentials here.

## Upstream Penpot AI Kit

The upstream kit remains external. Its preferred workflow for the first screen is `brief-to-screen`, using its screen-builder, design-quality and accessibility review behavior. The PinCommerce repo supplies the product context and constraints; the kit supplies design workflow discipline; Penpot MCP is the live execution bridge.

## Safety

- Never commit an MCP key, access token or credential-bearing MCP URL.
- CI does not connect to Penpot.
- `npm run penpot:check` is the required live target preflight before handing work to an MCP-capable design assistant.
- Meaningful canvas changes require the workflow's direction-approval checkpoint.
- The direct custom visual renderer is not the preferred design-generation path.
