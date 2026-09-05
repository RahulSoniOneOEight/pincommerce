# Live Penpot MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe local-Windows live sync client that reads the active Penpot file through Remote MCP, plans deterministic changes from the existing GitHub design manifests, applies only explicitly approved creates/updates, and verifies idempotent results.

**Architecture:** Keep the existing `PenpotAdapter` contract and introduce three isolated layers: `McpTransport` for MCP protocol connectivity, `PenpotMcpGateway` for capability discovery and Penpot-specific read/write semantics, and `McpPenpotAdapter` for PinCommerce operation orchestration. CLI commands `penpot:check`, `penpot:plan`, `penpot:sync -- --apply`, and `penpot:verify` use those layers; CI uses only fake transports and never real credentials.

**Tech Stack:** Node.js >=20, TypeScript, Vitest, Zod, `@modelcontextprotocol/sdk`, `dotenv`, existing PinCommerce manifest schemas and operation planner.

**Spec:** `docs/superpowers/specs/2026-09-06-live-penpot-mcp-design.md`

## Global Constraints

- GitHub remains the canonical desired state; Penpot is the live editable workspace.
- Local Windows runner only for live writes in v1.
- `PENPOT_MCP_URL` is required for remote operations and must never be logged or committed.
- No live mutation without explicit `--apply`.
- No deletion in v1; orphans are reported only.
- Read before write for every managed object.
- If the connected target file cannot be confidently identified, live sync must stop.
- Prototype links may be reported unsupported if the live MCP capability surface does not expose a safe matching operation.
- CI must pass without Penpot credentials or network access to Penpot.
- A second identical sync must produce zero creates/updates for supported managed fields.

---

## File Structure

Create or modify these focused units:

- `agent/penpot-sync/src/config.ts` — local environment parsing and secret-safe URL handling.
- `agent/penpot-sync/src/redact.ts` — credential redaction helpers.
- `agent/penpot-sync/src/mcp/types.ts` — stable transport and capability types.
- `agent/penpot-sync/src/mcp/transport.ts` — official MCP SDK client connection/list/call wrapper.
- `agent/penpot-sync/src/mcp/gateway.ts` — capability binding and normalized Penpot operations.
- `agent/penpot-sync/src/adapters/mcp.ts` — live adapter implementing `PenpotAdapter`.
- `agent/penpot-sync/src/livePlan.ts` — compare desired operations with inspected remote state.
- `agent/penpot-sync/src/liveCli.ts` — check/plan/sync/verify command orchestration.
- `agent/penpot-sync/test/fakes/fakeMcp.ts` — in-memory MCP fixture.
- `agent/penpot-sync/test/config.test.ts` — config and redaction tests.
- `agent/penpot-sync/test/gateway.test.ts` — discovery and normalized gateway tests.
- `agent/penpot-sync/test/livePlan.test.ts` — create/update/unchanged/orphan comparison tests.
- `agent/penpot-sync/test/liveCli.test.ts` — safety gating, no-write modes, verify and partial failure tests.
- `package.json` — add dependencies and local Penpot scripts.
- `.env.example` — expose names only.
- `README.md` — Windows operator flow.

---

### Task 1: Configuration and credential redaction

**Files:**
- Create: `agent/penpot-sync/src/config.ts`
- Create: `agent/penpot-sync/src/redact.ts`
- Test: `agent/penpot-sync/test/config.test.ts`
- Modify: `.env.example`

**Interfaces:**
- Produces: `loadPenpotConfig(env?: NodeJS.ProcessEnv): PenpotConfig`
- Produces: `redactUrl(value: string): string`
- `PenpotConfig = { mcpUrl: string; expectedFileId?: string }`

- [ ] **Step 1: Write failing tests for missing config and URL redaction**

```ts
import { describe, expect, it } from 'vitest';
import { loadPenpotConfig } from '../src/config.js';
import { redactUrl } from '../src/redact.js';

describe('Penpot config', () => {
  it('rejects missing PENPOT_MCP_URL', () => {
    expect(() => loadPenpotConfig({})).toThrow('CONFIG_ERROR');
  });

  it('redacts userToken query values', () => {
    expect(redactUrl('https://design.penpot.app/mcp/stream?userToken=secret123&x=1'))
      .toBe('https://design.penpot.app/mcp/stream?userToken=%5BREDACTED%5D&x=1');
  });
});
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run: `npm test -- --run agent/penpot-sync/test/config.test.ts`

Expected: FAIL because `config.ts` and `redact.ts` do not exist.

- [ ] **Step 3: Implement minimal config parsing and secret-safe redaction**

```ts
export type PenpotConfig = { mcpUrl: string; expectedFileId?: string };

export function loadPenpotConfig(env: NodeJS.ProcessEnv = process.env): PenpotConfig {
  const mcpUrl = env.PENPOT_MCP_URL?.trim();
  if (!mcpUrl) throw new Error('CONFIG_ERROR: PENPOT_MCP_URL is required');
  new URL(mcpUrl);
  return { mcpUrl, expectedFileId: env.PENPOT_FILE_ID?.trim() || undefined };
}
```

`redactUrl` must parse the URL and replace `userToken`, `token`, `key`, and `access_token` query values with `[REDACTED]` while preserving non-secret query parameters.

- [ ] **Step 4: Run tests**

Run: `npm test -- --run agent/penpot-sync/test/config.test.ts`

Expected: PASS.

- [ ] **Step 5: Update `.env.example`**

```text
PENPOT_MCP_URL=
PENPOT_FILE_ID=
OPENAI_API_KEY=
```

- [ ] **Step 6: Commit**

```bash
git add .env.example agent/penpot-sync/src/config.ts agent/penpot-sync/src/redact.ts agent/penpot-sync/test/config.test.ts
git commit -m "feat: add safe Penpot MCP configuration"
```

---

### Task 2: MCP transport abstraction and official SDK connection

**Files:**
- Create: `agent/penpot-sync/src/mcp/types.ts`
- Create: `agent/penpot-sync/src/mcp/transport.ts`
- Create: `agent/penpot-sync/test/fakes/fakeMcp.ts`
- Modify: `package.json`

**Interfaces:**
- Produces: `McpTool = { name: string; description?: string; inputSchema?: unknown }`
- Produces: `McpTransport = { connect(): Promise<void>; listTools(): Promise<McpTool[]>; callTool(name: string, args: Record<string, unknown>): Promise<unknown>; close(): Promise<void> }`
- Produces: `RemoteMcpTransport`

- [ ] **Step 1: Add dependency declarations**

Add runtime dependencies:

```json
"dependencies": {
  "@modelcontextprotocol/sdk": "^1.0.0",
  "dotenv": "^16.4.7"
}
```

Keep existing dev dependencies unchanged.

- [ ] **Step 2: Write a fake transport fixture**

The fake must record `calls`, expose a configurable `tools` list and configurable tool responses, and implement the exact `McpTransport` interface. It must never perform network I/O.

- [ ] **Step 3: Implement `RemoteMcpTransport` using the official MCP SDK**

Requirements:
- construct the SDK client only from `PenpotConfig.mcpUrl`;
- support connect/listTools/callTool/close;
- wrap connection failures as `MCP_CONNECT_ERROR` with `redactUrl(...)` output;
- never include raw MCP URL in thrown errors.

- [ ] **Step 4: Typecheck**

Run: `npm run typecheck`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add package.json agent/penpot-sync/src/mcp agent/penpot-sync/test/fakes/fakeMcp.ts
git commit -m "feat: add remote MCP transport"
```

---

### Task 3: Penpot MCP capability discovery and normalized gateway

**Files:**
- Create: `agent/penpot-sync/src/mcp/gateway.ts`
- Test: `agent/penpot-sync/test/gateway.test.ts`

**Interfaces:**
- Produces: `PenpotCapabilities`
- Produces: `PenpotRemoteObject = { repoId?: string; remoteId: string; kind: string; name?: string; payload?: unknown }`
- Produces: `PenpotMcpGateway`
- Methods: `discover()`, `inspectTarget()`, `listManagedObjects()`, `create(op)`, `update(op, current)`, `verify(op)`

- [ ] **Step 1: Write failing discovery tests**

Tests must prove:
- gateway calls `listTools()` exactly once per discovery cycle;
- read capability is required;
- missing write capability does not break read-only check/plan;
- unsupported prototype capability is surfaced as `supported: false`, not approximated.

- [ ] **Step 2: Run test and verify failure**

Run: `npm test -- --run agent/penpot-sync/test/gateway.test.ts`

Expected: FAIL because gateway does not exist.

- [ ] **Step 3: Implement semantic capability binding**

Binding rule: inspect live tool names, descriptions, and schemas and select tools by supported semantic role; keep the selected names inside `PenpotCapabilities`. Do not expose tool names to higher layers.

The gateway must stop with `MCP_CAPABILITY_ERROR` when it cannot bind a required read/inspect capability.

- [ ] **Step 4: Implement target inspection**

`inspectTarget()` must return a normalized target identity including file/page identifiers when discoverable. If `PENPOT_FILE_ID` is configured and differs from the connected target, throw `TARGET_ERROR` before any write.

- [ ] **Step 5: Run tests**

Run: `npm test -- --run agent/penpot-sync/test/gateway.test.ts`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add agent/penpot-sync/src/mcp/gateway.ts agent/penpot-sync/test/gateway.test.ts
git commit -m "feat: discover Penpot MCP capabilities"
```

---

### Task 4: Remote state comparison and non-destructive live plan

**Files:**
- Create: `agent/penpot-sync/src/livePlan.ts`
- Test: `agent/penpot-sync/test/livePlan.test.ts`

**Interfaces:**
- Consumes: existing `PenpotOperation[]`
- Consumes: `PenpotRemoteObject[]`
- Produces: `LivePlanItem = { repoId: string; action: 'create' | 'update' | 'unchanged' | 'orphan' | 'unsupported'; operation?: PenpotOperation; current?: PenpotRemoteObject }`
- Produces: `buildLivePlan(desired, current, capabilities): LivePlanItem[]`

- [ ] **Step 1: Write comparison tests**

Test cases:
- desired missing remotely => `create`;
- same stable `repoId` with materially different managed payload => `update`;
- equivalent managed payload => `unchanged`;
- remote managed item not in desired => `orphan`;
- unsupported prototype route => `unsupported`;
- no plan item ever emits `delete`.

- [ ] **Step 2: Run focused test and confirm failure**

Run: `npm test -- --run agent/penpot-sync/test/livePlan.test.ts`

Expected: FAIL because `livePlan.ts` does not exist.

- [ ] **Step 3: Implement deterministic comparison**

Normalize payload objects recursively with sorted object keys before deep comparison. Preserve array order. Sort final plan items by desired operation order, then append orphans sorted by `repoId`.

- [ ] **Step 4: Run tests**

Run: `npm test -- --run agent/penpot-sync/test/livePlan.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/penpot-sync/src/livePlan.ts agent/penpot-sync/test/livePlan.test.ts
git commit -m "feat: add live Penpot diff planner"
```

---

### Task 5: Idempotent `McpPenpotAdapter`

**Files:**
- Create: `agent/penpot-sync/src/adapters/mcp.ts`
- Modify: `agent/penpot-sync/src/adapter.ts`
- Test: `agent/penpot-sync/test/mcpAdapter.test.ts`

**Interfaces:**
- Implements existing `PenpotAdapter.apply(operations: PenpotOperation[]): Promise<SyncResult>`
- Produces: `McpPenpotAdapter`

- [ ] **Step 1: Write adapter tests**

Prove:
- create and update actions call gateway writes;
- unchanged/orphan/unsupported do not write;
- partial failures return `failed > 0` and include the failing `repoId`;
- successful items before a failure remain successful;
- repeating the same desired state against the updated fake remote state produces zero creates/updates.

- [ ] **Step 2: Run focused test and confirm failure**

Run: `npm test -- --run agent/penpot-sync/test/mcpAdapter.test.ts`

Expected: FAIL because adapter does not exist.

- [ ] **Step 3: Implement adapter orchestration**

Algorithm:
1. discover capabilities;
2. inspect target;
3. list current managed objects;
4. build live plan;
5. process actions in original operation order;
6. call create/update only;
7. collect counts and per-`repoId` errors;
8. never call delete.

- [ ] **Step 4: Run tests**

Run: `npm test -- --run agent/penpot-sync/test/mcpAdapter.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/penpot-sync/src/adapter.ts agent/penpot-sync/src/adapters/mcp.ts agent/penpot-sync/test/mcpAdapter.test.ts
git commit -m "feat: add idempotent live Penpot adapter"
```

---

### Task 6: Live CLI commands and write gate

**Files:**
- Create: `agent/penpot-sync/src/liveCli.ts`
- Test: `agent/penpot-sync/test/liveCli.test.ts`
- Modify: `package.json`

**Interfaces:**
- Produces: `runLive(argv?: string[], root?: string, deps?: LiveCliDeps): Promise<number>`
- Adds scripts: `penpot:check`, `penpot:plan`, `penpot:sync`, `penpot:verify`

- [ ] **Step 1: Write CLI safety tests**

Prove:
- `check` makes zero write calls;
- `plan` makes zero write calls;
- `sync` without `--apply` exits non-zero before any write;
- `sync --apply` invokes live adapter;
- `verify` makes zero write calls and exits non-zero on drift;
- all printed connection summaries redact credentials.

- [ ] **Step 2: Run focused test and confirm failure**

Run: `npm test -- --run agent/penpot-sync/test/liveCli.test.ts`

Expected: FAIL because live CLI does not exist.

- [ ] **Step 3: Implement command orchestration**

`check` output must include only target summary and capability names/booleans.

`plan` output must include counts:

```json
{"create":0,"update":0,"unchanged":0,"orphan":0,"unsupported":0}
```

`sync` must immediately reject when `--apply` is absent.

`verify` must re-read state and fail with `VERIFY_ERROR` if any supported desired object is absent or materially different.

- [ ] **Step 4: Add npm scripts**

```json
"penpot:check": "tsx agent/penpot-sync/src/liveCli.ts check",
"penpot:plan": "tsx agent/penpot-sync/src/liveCli.ts plan",
"penpot:sync": "tsx agent/penpot-sync/src/liveCli.ts sync",
"penpot:verify": "tsx agent/penpot-sync/src/liveCli.ts verify"
```

- [ ] **Step 5: Run tests and typecheck**

Run:

```bash
npm test -- --run agent/penpot-sync/test/liveCli.test.ts
npm run typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add package.json agent/penpot-sync/src/liveCli.ts agent/penpot-sync/test/liveCli.test.ts
git commit -m "feat: add guarded live Penpot CLI"
```

---

### Task 7: Windows operator documentation and CI regression contract

**Files:**
- Modify: `README.md`
- Modify: `.github/workflows/design-contract.yml`

**Interfaces:**
- No new runtime interfaces.

- [ ] **Step 1: Document exact local Windows flow**

README must include:

```powershell
git pull
npm install
Copy-Item .env.example .env
# edit .env and set PENPOT_MCP_URL
npm run penpot:check
npm run penpot:plan
npm run penpot:sync -- --apply
npm run penpot:verify
```

Also state: open the intended Penpot file first and use **File → MCP Server → Connect**; never paste the MCP key into GitHub or commit `.env`.

- [ ] **Step 2: Keep CI credential-free**

Update Design Contract only to run the full unit suite/typecheck/manifest validation/dry-run. Do not add any live Penpot command to GitHub Actions.

- [ ] **Step 3: Run the complete verification suite**

Run:

```bash
npm install
npm test -- --run
npm run typecheck
npm run validate
npm run sync:dry -- --out artifacts/penpot-plan.json
```

Expected: all commands PASS without `PENPOT_MCP_URL`.

- [ ] **Step 4: Secret scan**

Run:

```bash
git grep -nE 'userToken=[^<[:space:]]+|PENPOT_MCP_URL=https://'
```

Expected: no committed credential value; documentation may mention variable names only.

- [ ] **Step 5: Commit**

```bash
git add README.md .github/workflows/design-contract.yml
git commit -m "docs: add local Penpot MCP operator flow"
```

---

### Task 8: PR verification and live smoke-test handoff

**Files:**
- No production file changes unless verification reveals a defect.

**Interfaces:**
- Acceptance boundary for the feature branch.

- [ ] **Step 1: Run full CI-equivalent verification again**

```bash
npm test -- --run
npm run typecheck
npm run validate
npm run sync:dry -- --out artifacts/penpot-plan.json
```

Expected: PASS.

- [ ] **Step 2: Open a PR against `main`**

PR summary must state that live Penpot credentials are local-only and that CI tests use fake MCP transport.

- [ ] **Step 3: Confirm GitHub Actions passes**

Expected Design Contract workflow: success.

- [ ] **Step 4: Perform operator-controlled live smoke test on Windows**

With the target Penpot file open and MCP-connected locally:

```powershell
npm run penpot:check
npm run penpot:plan
```

Expected: both succeed with zero writes and no credential leakage.

Only after the plan is reviewed:

```powershell
npm run penpot:sync -- --apply
npm run penpot:verify
npm run penpot:plan
```

Expected final plan: `create=0`, `update=0` for supported managed objects; unmanaged objects remain untouched.
