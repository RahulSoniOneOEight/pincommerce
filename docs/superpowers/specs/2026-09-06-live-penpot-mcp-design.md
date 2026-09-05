# Live Penpot MCP Connection Design

## Goal

Add a safe live Penpot connection layer to `pincommerce` so the existing GitHub-defined design state can be inspected, compared, and applied to an actively connected Penpot file from a local Windows runner.

## Operating model

- GitHub remains the canonical desired state for foundations, themes, components, screens, and prototype routes.
- Penpot remains the live editable visual workspace.
- The sync client runs on the user's local Windows machine.
- The user opens the target Penpot file in the browser and connects it through **File → MCP Server → Connect** before live operations run.
- The client connects to Penpot's remote MCP endpoint using the user's MCP URL/key stored only in local environment variables.
- The MCP credential must never be committed, logged, included in dry-run artifacts, or sent to GitHub Actions.

## Scope

### In scope

1. MCP client transport for the remote Penpot MCP endpoint.
2. Read-only connectivity check.
3. Inspection of the currently connected Penpot file/page.
4. Diff between GitHub desired state and current Penpot state.
5. Idempotent create/update operations for:
   - pages
   - token sets/themes
   - components
   - screens/boards
   - prototype links where supported by the MCP tool surface
6. Explicitly gated live writes.
7. Post-write verification.
8. Local Windows setup documentation.
9. Unit tests with a fake MCP transport so CI never requires real Penpot credentials.

### Out of scope for first live version

- Automatic deletion of Penpot content.
- Background or server-side unattended syncing.
- GitHub Actions live writes to Penpot.
- Bidirectional Penpot → GitHub synchronization.
- Automatic publishing/exporting from Penpot.
- Direct manipulation of `.penpot` archive internals.

## Architecture

The current `PenpotAdapter` interface remains the stable application boundary.

```text
GitHub manifests
    ↓
loadProject()
    ↓
buildPlan()
    ↓
Desired Penpot operations
    ↓
McpPenpotAdapter
    ├─ inspect current Penpot state
    ├─ compute create/update/unchanged actions
    ├─ call remote Penpot MCP tools
    └─ verify resulting state
    ↓
Connected Penpot file
```

The MCP implementation is split into three isolated units:

1. **McpTransport** — protocol/client connection only. It knows how to connect, list tools, and invoke tools. It does not understand PinCommerce design semantics.
2. **PenpotMcpGateway** — maps Penpot-specific MCP tools/results into stable read/write methods such as `getPages`, `ensurePage`, `ensureTokens`, `ensureComponent`, `ensureScreen`, and `ensurePrototypeLink`.
3. **McpPenpotAdapter** — implements the existing `PenpotAdapter` contract and applies PinCommerce operations idempotently using the gateway.

This separation avoids coupling the whole sync engine to the exact current Penpot MCP tool names. If Penpot changes its MCP surface, only the gateway should normally change.

## Configuration

Local environment variables:

```text
PENPOT_MCP_URL=<full remote MCP URL copied from Penpot>
PENPOT_FILE_ID=<optional expected target file id when discoverable>
```

`PENPOT_MCP_URL` is required for any remote operation. The implementation must redact query-string credentials from errors and logs.

The existing `.env` ignore rules remain mandatory. `.env.example` will contain variable names only.

## Commands

### `npm run penpot:check`

Read-only. It should:

1. Validate configuration.
2. Connect to the remote MCP server.
3. Confirm the Penpot MCP tool surface is available.
4. Confirm a Penpot file/page is connected and inspectable.
5. Print a credential-free connection summary.

No writes are allowed.

### `npm run penpot:plan`

Read-only. It should:

1. Load and validate GitHub manifests.
2. Inspect current Penpot state.
3. Compare desired vs current state.
4. Produce a structured plan with counts for `create`, `update`, `unchanged`, and `orphan`.
5. Never delete or mutate Penpot content.

### `npm run penpot:sync -- --apply`

Live write mode. It must refuse to run unless `--apply` is present.

Execution order:

1. Foundations page/tokens
2. Theme A — BuildKart Green
3. Theme B — Premium Blue
4. Components
5. B2C screens
6. B2B screens
7. Prototype links

For every item, the adapter should read first and then:

- create if missing
- update if materially different
- do nothing if equivalent

Content present in Penpot but absent from GitHub is reported as an orphan and left untouched.

### `npm run penpot:verify`

Read-only post-sync verification. It re-reads Penpot and checks that all expected managed objects exist and match the supported managed properties.

## Managed identity and idempotency

Each GitHub-managed object already has a stable `repoId`, such as:

- `page:components`
- `tokens:theme-b-blue`
- `component:product-card`
- `screen:b2c-home`
- `route:b2c-home-product`

The live layer must maintain a deterministic mapping between `repoId` and the corresponding Penpot object. Where Penpot supports metadata/custom properties, use a managed marker. Otherwise maintain a local mapping file under `artifacts/` that is excluded from Git and can be regenerated by inspection when possible.

Human-readable names alone must not be treated as sufficient identity when a stronger identifier is available.

## Safety rules

- No live mutation without explicit `--apply`.
- No deletion in v1.
- No credential values in stdout/stderr, artifacts, tests, or exceptions.
- Network timeouts and MCP failures return non-zero exit status.
- Partial failures are reported per `repoId`.
- A failed operation does not trigger destructive rollback of prior successful operations.
- A second identical sync should result in zero creates/updates for supported managed fields.
- If the connected Penpot file cannot be confidently identified, live sync must stop rather than write to an uncertain target.

## Penpot MCP tool discovery

The implementation must not hard-code an assumed tool list before connecting. On `penpot:check`, the MCP client discovers the actual server tool surface and the gateway binds only to supported capabilities.

If a required capability is unavailable, the command must report it clearly. Prototype links are allowed to be reported as unsupported rather than approximated with unsafe or unrelated writes.

## Error handling

Errors are categorized as:

- `CONFIG_ERROR` — missing/invalid local configuration
- `MCP_CONNECT_ERROR` — remote transport failure
- `MCP_CAPABILITY_ERROR` — required Penpot MCP capability unavailable
- `TARGET_ERROR` — no active/valid Penpot target file
- `READ_ERROR` — Penpot state inspection failed
- `WRITE_ERROR` — create/update failed
- `VERIFY_ERROR` — post-write state does not match expected state

Every reported error includes the relevant `repoId` where applicable, but never secrets.

## Testing

CI uses only fake/in-memory MCP transport fixtures.

Required tests:

- URL/key redaction
- tool discovery and capability binding
- connection check succeeds with fake Penpot MCP
- check mode performs zero writes
- plan mode performs zero writes
- sync refuses without `--apply`
- missing objects produce creates
- changed objects produce updates
- equivalent objects remain unchanged
- orphans are reported but not deleted
- partial write errors are surfaced by `repoId`
- repeated identical sync is idempotent
- verify detects drift

Existing dry-run and design-contract tests remain green.

## Local Windows usage

Expected operator flow:

1. Pull `pincommerce`.
2. Run `npm install`.
3. Create a local `.env` containing `PENPOT_MCP_URL`.
4. Open the target Penpot file in the browser.
5. Use **File → MCP Server → Connect** in Penpot.
6. Run `npm run penpot:check`.
7. Run `npm run penpot:plan` and review the planned changes.
8. Run `npm run penpot:sync -- --apply`.
9. Run `npm run penpot:verify`.

## Acceptance criteria

The feature is complete when:

1. A local Windows user can validate a remote Penpot MCP connection without exposing the credential.
2. The client can inspect the active Penpot design context.
3. A read-only plan distinguishes create/update/unchanged/orphan operations.
4. Live sync requires explicit `--apply`.
5. The sync creates/updates supported design objects without deleting unmanaged content.
6. A second identical run is idempotent.
7. Verification confirms managed design state after sync.
8. All CI tests pass without requiring a real Penpot account or secret.
