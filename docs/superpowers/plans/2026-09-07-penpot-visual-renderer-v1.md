# Penpot Visual Renderer v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a production-like Theme B Premium Blue commerce design system into the already-managed Penpot objects, covering reusable core components plus B2C Home, Category, and Product screens with deterministic, idempotent live sync.

**Architecture:** Keep GitHub as desired-state source and extend the existing Penpot MCP `execute_code` gateway. Add declarative visual manifests, a small typed render model, a compiler that emits controlled Penpot Plugin API code, and managed-subtree reconciliation that updates existing component/screen roots without creating duplicates or touching unrelated shapes.

**Tech Stack:** TypeScript, Node 20+, Zod, Vitest, JSON manifests, Penpot Remote MCP via `@modelcontextprotocol/sdk`, Penpot Plugin API through `execute_code`.

**Spec:** `docs/superpowers/specs/2026-09-07-penpot-visual-renderer-v1-design.md`

## Global Constraints

- Theme B — Premium Blue only in this wave.
- Hybrid asset strategy: editable category icon geometry + deterministic product-image placeholders; no external image dependency.
- Reuse existing managed `repoId` roots and `pincommerce.managed.v1`; do not introduce a second root registry.
- No direct `.penpot` archive manipulation.
- Read-before-write and explicit `--apply` remain mandatory.
- No deletes of managed roots or unrelated user content.
- Prototype-link creation remains unsupported in this wave.
- Same desired state synced twice must yield zero creates and zero updates for supported objects.
- Live writes remain local/operator-driven; CI uses fakes only and requires no Penpot credential.

---

## File Structure

### New desired-state files

- `design-system/visual/theme-b.json` — resolved Theme B rendering roles and numeric layout values derived from canonical tokens.
- `design-system/visual/components.json` — visual composition definitions for v1 reusable components.
- `design-system/visual/assets.json` — deterministic category-icon and product-placeholder recipes.
- `screens/b2c/visual-v1.json` — sample content and section composition for Home, Category, Product.

### New renderer source

- `agent/penpot-sync/src/visual/schema.ts` — Zod schemas and TypeScript types for visual manifests and render nodes.
- `agent/penpot-sync/src/visual/loadVisualProject.ts` — load/validate visual JSON and confirm referenced component/screen IDs exist.
- `agent/penpot-sync/src/visual/renderModel.ts` — normalize manifests into deterministic render trees and stable fingerprints.
- `agent/penpot-sync/src/visual/compiler.ts` — compile normalized render trees into Penpot Plugin API JavaScript snippets.
- `agent/penpot-sync/src/visual/registry.ts` — renderer version/fingerprint helpers stored alongside current registry entries.

### Modified live sync source

- `agent/penpot-sync/src/mcp/gateway.ts` — add read/render methods for managed root lookup and renderer-owned subtree reconciliation.
- `agent/penpot-sync/src/livePlan.ts` — visual fingerprint affects update/unchanged classification for only v1 target components/screens.
- `agent/penpot-sync/src/adapters/mcp.ts` — apply visual render updates after managed root exists.
- `agent/penpot-sync/src/liveCli.ts` — load visual desired state for plan/sync/verify without changing command contract.

### Tests

- `agent/penpot-sync/test/visualSchema.test.ts`
- `agent/penpot-sync/test/visualLoad.test.ts`
- `agent/penpot-sync/test/renderModel.test.ts`
- `agent/penpot-sync/test/compiler.test.ts`
- `agent/penpot-sync/test/visualLivePlan.test.ts`
- `agent/penpot-sync/test/visualGateway.test.ts`
- extend `agent/penpot-sync/test/mcpAdapter.test.ts`
- extend `agent/penpot-sync/test/liveCli.test.ts`

---

### Task 1: Add Visual Manifest Schemas and Theme B Desired State

**Files:**
- Create: `design-system/visual/theme-b.json`
- Create: `design-system/visual/components.json`
- Create: `design-system/visual/assets.json`
- Create: `screens/b2c/visual-v1.json`
- Create: `agent/penpot-sync/src/visual/schema.ts`
- Test: `agent/penpot-sync/test/visualSchema.test.ts`

**Interfaces:**
- Consumes: existing `design-system/tokens/theme-b-blue.json`, `design-system/components/catalog.json`, `screens/b2c/screens.json`.
- Produces: `VisualTheme`, `VisualComponentDefinition`, `VisualAssetDefinition`, `VisualScreenDefinition`, `VisualProjectInput` Zod schemas/types.

- [ ] **Step 1: Write the failing schema test**

```ts
import { describe, expect, it } from 'vitest';
import { VisualProjectInputSchema } from '../src/visual/schema.js';

describe('VisualProjectInputSchema', () => {
  it('accepts the v1 Theme B renderer contract and rejects external image URLs', () => {
    const parsed = VisualProjectInputSchema.parse({
      theme: {
        id: 'theme-b',
        canvas: { width: 390, height: 844 },
        colors: { primary: '#123456', background: '#ffffff', surface: '#f5f7fb', text: '#101828', textMuted: '#667085', border: '#d0d5dd', accent: '#d4a72c', primaryForeground: '#ffffff' },
        spacing: { xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 24 },
        radius: { sm: 8, md: 12, lg: 16 },
        watermarkOpacity: 0.03
      },
      components: [{ id: 'button', variants: ['primary'], root: { id: 'root', type: 'frame', children: [] } }],
      assets: [{ id: 'category-plumbing', kind: 'category-icon', recipe: 'plumbing' }],
      screens: [{ id: 'b2c-home', title: 'Home', sections: [] }]
    });
    expect(parsed.theme.id).toBe('theme-b');
    expect(() => VisualProjectInputSchema.parse({ ...parsed, assets: [{ id: 'remote', kind: 'image', url: 'https://example.com/x.png' }] })).toThrow();
  });
});
```

- [ ] **Step 2: Run the test and confirm RED**

Run:

```bash
npm test -- --run agent/penpot-sync/test/visualSchema.test.ts
```

Expected: FAIL because `../src/visual/schema.js` does not exist.

- [ ] **Step 3: Implement the minimal schemas**

`schema.ts` must define a deliberately small render-node union:

```ts
export const RenderNodeSchema = z.lazy(() => z.discriminatedUnion('type', [
  z.object({ id:z.string(), type:z.literal('frame'), x:z.number().optional(), y:z.number().optional(), width:z.number(), height:z.number(), fill:z.string().optional(), radius:z.number().optional(), children:z.array(RenderNodeSchema).default([]) }),
  z.object({ id:z.string(), type:z.literal('rect'), x:z.number(), y:z.number(), width:z.number(), height:z.number(), fill:z.string(), radius:z.number().optional(), opacity:z.number().min(0).max(1).optional() }),
  z.object({ id:z.string(), type:z.literal('text'), x:z.number(), y:z.number(), width:z.number().optional(), text:z.string(), role:z.enum(['display','title','body','label','caption','price']), color:z.string().optional(), size:z.number().optional(), weight:z.number().optional() }),
  z.object({ id:z.string(), type:z.literal('icon'), x:z.number(), y:z.number(), width:z.number(), height:z.number(), recipe:z.string(), color:z.string().optional() }),
  z.object({ id:z.string(), type:z.literal('component-instance'), x:z.number(), y:z.number(), componentId:z.string(), variant:z.string().optional(), props:z.record(z.unknown()).default({}) })
]));
```

Also define schemas for theme, component definitions, deterministic asset recipes, screen sections, and top-level input. Reject any asset shape containing URL/network fields.

- [ ] **Step 4: Add the actual v1 JSON manifests**

`theme-b.json` must contain resolved roles for the current Premium Blue theme, 390×844 canvas, 2–4% watermark opacity, spacing/radius values, and no external URLs.

`components.json` must define v1 visual structures for:

```text
header
search-bar
category-chip
brand-chip
product-card
price-block
quantity-control
button
bottom-nav
badge
```

`assets.json` must define recipes for:

```text
category-plumbing
category-electrical
category-sanitary
category-paints-construction
category-hardware-tools
category-agriculture
product-placeholder-primary
product-placeholder-secondary
```

`screens/b2c/visual-v1.json` must define only:

```text
b2c-home
b2c-category
b2c-product
```

with deterministic sample copy and products; do not add network assets.

- [ ] **Step 5: Re-run test and commit**

```bash
npm test -- --run agent/penpot-sync/test/visualSchema.test.ts
git add design-system/visual screens/b2c/visual-v1.json agent/penpot-sync/src/visual/schema.ts agent/penpot-sync/test/visualSchema.test.ts
git commit -m "feat: define Penpot visual renderer manifests"
```

Expected: PASS.

---

### Task 2: Load and Validate Visual Project Against Existing Catalogs

**Files:**
- Create: `agent/penpot-sync/src/visual/loadVisualProject.ts`
- Test: `agent/penpot-sync/test/visualLoad.test.ts`

**Interfaces:**
- Consumes: `VisualProjectInputSchema` and repository root path.
- Produces: `loadVisualProject(root: string): Promise<VisualProjectInput>`.

- [ ] **Step 1: Write failing tests**

```ts
it('loads the four visual files and validates component/screen references', async () => {
  const visual = await loadVisualProject(process.cwd());
  expect(visual.theme.id).toBe('theme-b');
  expect(visual.screens.map(x => x.id)).toEqual(['b2c-home','b2c-category','b2c-product']);
});

it('rejects a visual screen that references an unknown component', async () => {
  // fixture root contains visual-v1.json referencing component:not-real
  await expect(loadVisualProject(fixtureRoot)).rejects.toThrow('VISUAL_VALIDATION_ERROR');
});
```

- [ ] **Step 2: Run tests and confirm RED**

```bash
npm test -- --run agent/penpot-sync/test/visualLoad.test.ts
```

Expected: FAIL because loader does not exist.

- [ ] **Step 3: Implement loader**

The loader must:

1. read the four new JSON files;
2. parse with `VisualProjectInputSchema`;
3. read `design-system/components/catalog.json` and `screens/b2c/screens.json`;
4. ensure every visual component id exists in catalog;
5. ensure every visual screen id exists in B2C screen manifest;
6. ensure every `component-instance` node references a known component id;
7. throw errors prefixed `VISUAL_VALIDATION_ERROR:`.

- [ ] **Step 4: Run tests and commit**

```bash
npm test -- --run agent/penpot-sync/test/visualLoad.test.ts
git add agent/penpot-sync/src/visual/loadVisualProject.ts agent/penpot-sync/test/visualLoad.test.ts
git commit -m "feat: load and validate visual project"
```

Expected: PASS.

---

### Task 3: Build Deterministic Render Trees and Fingerprints

**Files:**
- Create: `agent/penpot-sync/src/visual/renderModel.ts`
- Create: `agent/penpot-sync/src/visual/registry.ts`
- Test: `agent/penpot-sync/test/renderModel.test.ts`

**Interfaces:**
- Consumes: `VisualProjectInput`.
- Produces:

```ts
export type VisualRenderTarget = {
  repoId: string;
  targetKind: 'component'|'screen';
  renderVersion: 'v1';
  tree: RenderNode;
  fingerprint: string;
};

export function buildVisualRenderTargets(input: VisualProjectInput): VisualRenderTarget[];
export function stableVisualFingerprint(value: unknown): string;
```

- [ ] **Step 1: Write failing deterministic tests**

```ts
it('builds only the v1 component and three screen targets with stable fingerprints', () => {
  const first = buildVisualRenderTargets(project);
  const second = buildVisualRenderTargets(JSON.parse(JSON.stringify(project)));
  expect(first.map(x => x.repoId)).toEqual(second.map(x => x.repoId));
  expect(first.map(x => x.fingerprint)).toEqual(second.map(x => x.fingerprint));
  expect(first.filter(x => x.targetKind === 'screen').map(x => x.repoId)).toEqual([
    'screen:b2c-home','screen:b2c-category','screen:b2c-product'
  ]);
});
```

- [ ] **Step 2: Run tests and confirm RED**

```bash
npm test -- --run agent/penpot-sync/test/renderModel.test.ts
```

- [ ] **Step 3: Implement normalized render targets**

Rules:

- Stable sort object keys before fingerprinting.
- Preserve arrays because screen/component visual ordering is meaningful.
- Fingerprint with Node `crypto.createHash('sha256')` over normalized JSON.
- Convert component ids to existing roots `component:<id>`.
- Convert screen ids to existing roots `screen:<id>`.
- Include render version and theme id in fingerprint input.
- No prototype routes or non-v1 screens become visual targets.

- [ ] **Step 4: Run tests and commit**

```bash
npm test -- --run agent/penpot-sync/test/renderModel.test.ts
git add agent/penpot-sync/src/visual/renderModel.ts agent/penpot-sync/src/visual/registry.ts agent/penpot-sync/test/renderModel.test.ts
git commit -m "feat: build deterministic visual render targets"
```

---

### Task 4: Compile Render Trees to Controlled Penpot Plugin API Code

**Files:**
- Create: `agent/penpot-sync/src/visual/compiler.ts`
- Test: `agent/penpot-sync/test/compiler.test.ts`

**Interfaces:**
- Consumes: `VisualRenderTarget` and resolved managed root id.
- Produces:

```ts
export function compileVisualRenderCode(target: VisualRenderTarget, remoteRootId: string): string;
```

- [ ] **Step 1: Write failing compiler tests**

```ts
it('emits managed-child names and never deletes the managed root', () => {
  const code = compileVisualRenderCode(target, 'root-123');
  expect(code).toContain('PCV1::component:button::');
  expect(code).toContain("getShapeById('root-123')");
  expect(code).not.toContain("root.remove()");
});

it('contains no network primitives', () => {
  const code = compileVisualRenderCode(target, 'root-123');
  expect(code).not.toMatch(/fetch\(|XMLHttpRequest|https?:\/\//);
});
```

- [ ] **Step 2: Run tests and confirm RED**

```bash
npm test -- --run agent/penpot-sync/test/compiler.test.ts
```

- [ ] **Step 3: Implement compiler helpers**

Compiler rules:

- Resolve root through a safe file/root lookup using the provided remote id.
- Renderer-owned child names use `PCV1::<repoId>::<nodeId>`.
- Remove/rebuild only existing descendants whose names start with `PCV1::<repoId>::`.
- Create supported primitives with Penpot Plugin API: boards/rectangles/text; use deterministic native geometry for icons.
- For `component-instance`, compile to a renderer-managed group/frame representation unless the current Penpot Plugin API supports safe instance lookup/creation in the active environment; do not invent an API call.
- Apply fill, radius, opacity, text content/size/weight, and deterministic x/y geometry.
- Use no external fetch or image import.
- Return `{repoId, fingerprint, rendered:true}`.

The generated code must never remove the managed root itself or inspect/delete unrelated descendants.

- [ ] **Step 4: Run tests and commit**

```bash
npm test -- --run agent/penpot-sync/test/compiler.test.ts
git add agent/penpot-sync/src/visual/compiler.ts agent/penpot-sync/test/compiler.test.ts
git commit -m "feat: compile visual trees for Penpot"
```

---

### Task 5: Extend Gateway for Managed Visual Rendering

**Files:**
- Modify: `agent/penpot-sync/src/mcp/gateway.ts`
- Test: `agent/penpot-sync/test/visualGateway.test.ts`

**Interfaces:**
- Consumes: existing managed registry entry + `VisualRenderTarget`.
- Produces:

```ts
renderVisual(target: VisualRenderTarget, current: PenpotRemoteObject): Promise<void>
```

and registry metadata:

```ts
visual?: { version: 'v1'; fingerprint: string }
```

- [ ] **Step 1: Write failing gateway tests**

```ts
it('renders into the existing managed root and records the visual fingerprint', async () => {
  const current = { repoId:'screen:b2c-home', remoteId:'screen-root', kind:'ensure-screen', payload:{} };
  await gateway.renderVisual(target, current as any);
  expect(fake.calls.at(-1)?.name).toBe('execute_code');
  expect(fake.calls.at(-1)?.args.code).toContain('screen-root');
  expect(fake.calls.at(-1)?.args.code).toContain(target.fingerprint);
});

it('refuses visual rendering when the managed root is missing', async () => {
  await expect(gateway.renderVisual(target, { repoId:target.repoId, remoteId:'', kind:'ensure-screen' } as any)).rejects.toThrow('VISUAL_TARGET_ERROR');
});
```

- [ ] **Step 2: Run and confirm RED**

```bash
npm test -- --run agent/penpot-sync/test/visualGateway.test.ts
```

- [ ] **Step 3: Implement `renderVisual`**

Behavior:

1. require `current.remoteId`;
2. compile visual code via `compileVisualRenderCode`;
3. execute it through existing `execute_code` transport;
4. after success, update only that registry entry to include `visual.version` and `visual.fingerprint`;
5. preserve existing `kind`, `name`, and desired `payload`;
6. redact any execution errors through existing error/redaction patterns.

- [ ] **Step 4: Run tests and commit**

```bash
npm test -- --run agent/penpot-sync/test/visualGateway.test.ts
git add agent/penpot-sync/src/mcp/gateway.ts agent/penpot-sync/test/visualGateway.test.ts
git commit -m "feat: render managed visual subtrees"
```

---

### Task 6: Make Live Plan Visual-Fingerprint Aware

**Files:**
- Modify: `agent/penpot-sync/src/livePlan.ts`
- Test: `agent/penpot-sync/test/visualLivePlan.test.ts`

**Interfaces:**
- Consumes: existing `PenpotOperation[]`, current registry objects, and `VisualRenderTarget[]`.
- Produces an extended plan item that can distinguish structural drift from visual drift without changing existing action names.

Suggested interface:

```ts
export function buildLivePlan(
  desired: PenpotOperation[],
  current: PenpotRemoteObject[],
  capabilities: PenpotCapabilities,
  visualTargets?: VisualRenderTarget[]
): LivePlanItem[];
```

- [ ] **Step 1: Write failing tests**

```ts
it('marks an otherwise unchanged screen as update when visual fingerprint differs', () => {
  const plan = buildLivePlan(desired, [{
    repoId:'screen:b2c-home', remoteId:'1', kind:'ensure-screen', payload:{}, visual:{version:'v1',fingerprint:'old'}
  } as any], caps, [{ repoId:'screen:b2c-home', targetKind:'screen', renderVersion:'v1', tree:{} as any, fingerprint:'new' }]);
  expect(plan.find(x => x.repoId === 'screen:b2c-home')?.action).toBe('update');
});

it('is unchanged when both structural state and visual fingerprint match', () => {
  // same setup, fingerprint new/new
});
```

- [ ] **Step 2: Run and confirm RED**

```bash
npm test -- --run agent/penpot-sync/test/visualLivePlan.test.ts
```

- [ ] **Step 3: Implement visual drift comparison**

Rules:

- Existing structural comparison remains unchanged for all 44 managed objects.
- Only repoIds present in `visualTargets` receive visual fingerprint comparison.
- Missing current visual fingerprint means `update`, not `create`, because root already exists.
- Prototype routes remain `unsupported` before visual comparison.
- Orphan behavior is unchanged.

- [ ] **Step 4: Run tests and commit**

```bash
npm test -- --run agent/penpot-sync/test/visualLivePlan.test.ts agent/penpot-sync/test/livePlan.test.ts
git add agent/penpot-sync/src/livePlan.ts agent/penpot-sync/test/visualLivePlan.test.ts
git commit -m "feat: plan visual renderer drift"
```

---

### Task 7: Apply Visual Updates Through the Existing MCP Adapter

**Files:**
- Modify: `agent/penpot-sync/src/adapters/mcp.ts`
- Test: `agent/penpot-sync/test/mcpAdapter.test.ts`

**Interfaces:**
- Consumes: `VisualRenderTarget[]` passed to adapter/apply path.
- Produces the existing `SyncResult` while ensuring structural create/update happens before visual rendering for the same repoId.

- [ ] **Step 1: Add failing adapter tests**

```ts
it('renders visuals after the managed root exists and does not create a second root', async () => {
  // current contains existing screen:b2c-home root with missing visual fingerprint
  // apply plan should call gateway.renderVisual once and gateway.create zero times for that repoId
});

it('reports a visual render failure as a per-repo write error without rolling back other roots', async () => {
  // one visual target throws; another succeeds
});
```

- [ ] **Step 2: Run and confirm RED**

```bash
npm test -- --run agent/penpot-sync/test/mcpAdapter.test.ts
```

- [ ] **Step 3: Implement minimal adapter integration**

Behavior:

- Build map `visualTargetByRepoId`.
- For `create`: perform structural create, refresh or synthesize current root, then render visual target if one exists.
- For `update`: perform structural update only if structurally required; render visual if visual fingerprint differs.
- For unchanged structural objects with visual drift, render visual and count as `updated`.
- Do not render unsupported prototype items.
- Keep partial-failure semantics and no destructive rollback.

- [ ] **Step 4: Run tests and commit**

```bash
npm test -- --run agent/penpot-sync/test/mcpAdapter.test.ts
git add agent/penpot-sync/src/adapters/mcp.ts agent/penpot-sync/test/mcpAdapter.test.ts
git commit -m "feat: apply visual renderer updates"
```

---

### Task 8: Wire Visual Desired State Into `check/plan/sync/verify`

**Files:**
- Modify: `agent/penpot-sync/src/liveCli.ts`
- Test: `agent/penpot-sync/test/liveCli.test.ts`

**Interfaces:**
- Consumes: `loadVisualProject(root)` and `buildVisualRenderTargets()`.
- Produces same CLI commands and JSON-compatible output contract.

- [ ] **Step 1: Add failing CLI tests**

```ts
it('plan reports visual updates when managed roots exist but fingerprints are absent', async () => {
  const code = await runLive(['plan'], fixtureRoot, deps);
  expect(code).toBe(0);
  expect(output).toContain('"update":');
});

it('verify fails on visual drift and remains read-only', async () => {
  const code = await runLive(['verify'], fixtureRoot, deps);
  expect(code).toBe(1);
  expect(fakeTransport.writeCalls).toBe(0);
});
```

- [ ] **Step 2: Run and confirm RED**

```bash
npm test -- --run agent/penpot-sync/test/liveCli.test.ts
```

- [ ] **Step 3: Integrate visual loader/model**

For `plan`, `sync`, and `verify`:

```ts
const visualProject = await loadVisualProject(root);
const visualTargets = buildVisualRenderTargets(visualProject);
```

Pass `visualTargets` into live plan / adapter. `check` remains only connectivity/capability/target and must not require visual rendering work beyond config/load sanity.

Preserve existing output keys:

```text
create
update
unchanged
orphan
unsupported
```

Do not print fingerprints or raw MCP data by default.

- [ ] **Step 4: Run tests and commit**

```bash
npm test -- --run agent/penpot-sync/test/liveCli.test.ts
git add agent/penpot-sync/src/liveCli.ts agent/penpot-sync/test/liveCli.test.ts
git commit -m "feat: wire visual renderer into live sync commands"
```

---

### Task 9: Contract Validation and Operator Documentation

**Files:**
- Modify: `README.md`
- Modify: `.github/workflows/design-contract.yml` only if current workflow does not already execute the full test/typecheck/validate suite needed for new files.
- Test: existing full suite.

**Interfaces:**
- Consumes: completed renderer.
- Produces: documented local operator flow and CI contract.

- [ ] **Step 1: Update README with the first visual render wave**

Document:

```text
1. Open intended Penpot file and connect MCP.
2. git checkout feat/penpot-visual-renderer-v1 / pull latest while PR is under review.
3. npm install
4. npm run penpot:check
5. npm run penpot:plan
6. Review expected visual updates for core components + Home/Category/Product.
7. npm run penpot:sync -- --apply
8. npm run penpot:verify
9. npm run penpot:plan
```

Explain that v1 renders Theme B only, uses native category icons and offline product placeholders, and does not create prototype links.

- [ ] **Step 2: Run full local/CI-equivalent validation**

```bash
npm test -- --run
npm run typecheck
npm run validate
npm run sync:dry -- --out artifacts/penpot-plan.json
```

Expected: all commands succeed.

- [ ] **Step 3: Commit**

```bash
git add README.md .github/workflows/design-contract.yml
git commit -m "docs: document Penpot visual renderer flow"
```

If workflow requires no change, commit only README.

---

### Task 10: Open PR and Perform Live Smoke Test Before Merge

**Files:**
- No production-file changes required unless smoke test exposes a defect.

**Interfaces:**
- Produces: reviewed PR and evidence that the live Penpot update is idempotent.

- [ ] **Step 1: Open PR**

Title:

```text
Add Penpot Visual Renderer v1
```

Body must summarize:

- declarative Theme B visual manifests;
- hybrid category-icon/product-placeholder assets;
- managed visual subtree renderer;
- Home/Category/Product visual composition;
- no deletes, no prototype links, no network images;
- visual fingerprint idempotency.

- [ ] **Step 2: Wait for Design Contract CI**

Required checks:

```text
npm install
npm test -- --run
npm run typecheck
npm run validate
npm run sync:dry
```

Expected: all green.

- [ ] **Step 3: Operator live plan**

On Windows in the repo root with Penpot file connected:

```cmd
npm run penpot:check
npm run penpot:plan
```

Expected on the already-synced file: `create:0`; updates should be limited to the v1 visual targets plus any intentional manifest changes. Do not hard-code a count in tests or docs because exact component target count is derived from manifest contents.

- [ ] **Step 4: Operator apply and verify**

```cmd
npm run penpot:sync -- --apply
npm run penpot:verify
npm run penpot:plan
```

Acceptance:

- sync result has `failed:0`;
- Home, Category, Product are visibly rendered in Theme B;
- category icon geometry is editable;
- product media uses offline deterministic placeholders;
- unrelated Penpot content remains untouched;
- final plan shows `create:0` and `update:0` for supported objects;
- prototype route intents remain `unsupported` rather than being approximated.

- [ ] **Step 5: Only then merge the PR**

Use squash merge after CI + live smoke are both clean.
