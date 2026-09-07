# Penpot AI Kit Control Plane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic GitHub-side design control plane that validates PinCommerce screen briefs, emits Penpot AI Kit-compatible handoff prompts and stable run manifests, while retaining the existing Penpot MCP preflight and de-emphasizing the custom visual renderer.

**Architecture:** `design-agent/` holds workflow policy and screen briefs. `agent/design-control/` provides a small offline TypeScript CLI for validation, brief generation and deterministic run manifests; it never calls Penpot or reads MCP secrets. CI validates this contract alongside the existing Penpot structural contract.

**Tech Stack:** Node.js 20+, TypeScript, TSX, Zod, Vitest, Markdown/JSON, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-07-penpot-ai-kit-control-plane-design.md`

## Global Constraints

- GitHub remains authoritative for product brief, journeys, themes, semantic-token constraints, component inventory, acceptance criteria and design-run records.
- Penpot AI Kit is referenced as an external workflow/skill layer; do not vendor its implementation or secrets into this repo.
- Existing `penpot:check` remains the live target preflight.
- `agent/design-control/` must never write directly to Penpot.
- No MCP key, full MCP URL or other secret may be emitted into generated briefs, manifests, logs or CI artifacts.
- CI must remain offline from live Penpot.
- Custom visual renderer remains available only as experimental/backwards-compatible tooling in this wave.
- First production brief is `b2c-home`, 390×844, Theme B Premium Blue, using the shared Make project as the reference direction.

---

### Task 1: Design-agent schema and validator

**Files:**
- Create: `agent/design-control/src/schema.ts`
- Create: `agent/design-control/src/loadDesignAgent.ts`
- Create: `agent/design-control/test/loadDesignAgent.test.ts`
- Create: `design-agent/config.json`
- Create: `design-agent/briefs/_template.md`
- Create: `design-agent/briefs/b2c-home.md`
- Create: `design-agent/runs/.gitkeep`

**Interfaces:**
- Produces `loadDesignAgent(rootDir:string): Promise<DesignAgentProject>`.
- `DesignAgentProject` includes parsed config, discovered brief metadata and raw brief Markdown.
- Validation rejects missing required headings, unknown workflow names, missing viewport/theme/acceptance sections and secret-like values.

- [ ] **Step 1: Write failing validator tests**

```ts
import { describe, expect, it } from 'vitest';
import { loadDesignAgent } from '../src/loadDesignAgent.js';

describe('design agent project',()=>{
  it('loads the production b2c-home brief',async()=>{
    const project=await loadDesignAgent(process.cwd());
    expect(project.config.defaultWorkflow).toBe('brief-to-screen');
    expect(project.briefs.get('b2c-home')?.viewport).toBe('390x844');
  });
  it('contains no secret-bearing values',async()=>{
    const project=await loadDesignAgent(process.cwd());
    expect(JSON.stringify(project)).not.toMatch(/userToken=|PENPOT_MCP_URL|sk-[A-Za-z0-9_-]+/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run agent/design-control/test/loadDesignAgent.test.ts`
Expected: FAIL because the design-control loader does not exist.

- [ ] **Step 3: Implement config/brief schemas and loader**

Create Zod schemas with these exact config fields:

```ts
export const designAgentConfigSchema=z.object({
  version:z.literal('v1'),
  provider:z.literal('penpot-ai-kit'),
  defaultWorkflow:z.literal('brief-to-screen'),
  requiredCheckpoints:z.array(z.enum(['direction-approval','design-quality','accessibility','visual-approval'])),
  allowedThemes:z.array(z.enum(['theme-a-green','theme-b-blue'])),
  preferredViewport:z.string().regex(/^\d+x\d+$/),
  upstream:z.object({repository:z.literal('penpot/penpot-ai-kit'),mode:z.literal('external')})
});
```

Parse each Markdown brief using required headings `## Context`, `## Objective`, `## Inputs`, `## Constraints`, `## Acceptance Criteria`, plus metadata lines `Screen:`, `Workflow:`, `Viewport:`, `Theme:`. Reject secret-like text matching `userToken=`, `PENPOT_MCP_URL`, `OPENAI_API_KEY`, `sk-`.

- [ ] **Step 4: Add production config/template/Home brief**

`design-agent/config.json` must select `brief-to-screen`, require all four checkpoints, allow both themes, and mark `penpot/penpot-ai-kit` as external.

`b2c-home.md` must require: branded header, search, commerce hero inspired by shared Make home, category shortcuts, Top Brands, Flash Deals, Top Rated Products, bottom navigation, 390×844 viewport, Theme B Premium Blue, 4px spacing rhythm, editable Penpot-native output, WCAG AA and visual review.

- [ ] **Step 5: Run tests**

Run: `npm test -- --run agent/design-control/test/loadDesignAgent.test.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add agent/design-control design-agent
git commit -m "feat: add design agent contract validation"
```

---

### Task 2: Handoff prompt and deterministic run manifest

**Files:**
- Create: `agent/design-control/src/handoff.ts`
- Create: `agent/design-control/src/runManifest.ts`
- Create: `agent/design-control/test/handoff.test.ts`
- Create: `agent/design-control/test/runManifest.test.ts`

**Interfaces:**
- `buildHandoff(project:DesignAgentProject, screenId:string): string`
- `buildRunManifest(project:DesignAgentProject, screenId:string): DesignRunManifest`
- Manifest fields: `version`, `screenId`, `workflow`, `viewport`, `theme`, `briefSha256`, `configSha256`, `requiredCheckpoints`, `inputs`.
- Manifest contains no current timestamp so identical inputs produce byte-identical JSON.

- [ ] **Step 1: Write failing handoff/manifest tests**

```ts
it('builds a self-contained Penpot AI Kit handoff',async()=>{
  const project=await loadDesignAgent(process.cwd());
  const text=buildHandoff(project,'b2c-home');
  expect(text).toContain('brief-to-screen');
  expect(text).toContain('390x844');
  expect(text).toContain('Theme B');
  expect(text).toContain('Flash Deals');
  expect(text).not.toMatch(/userToken=|PENPOT_MCP_URL/);
});

it('is deterministic',async()=>{
  const project=await loadDesignAgent(process.cwd());
  expect(buildRunManifest(project,'b2c-home')).toEqual(buildRunManifest(project,'b2c-home'));
});
```

- [ ] **Step 2: Run tests and observe failure**

Run: `npm test -- --run agent/design-control/test/handoff.test.ts agent/design-control/test/runManifest.test.ts`
Expected: FAIL because builders do not exist.

- [ ] **Step 3: Implement handoff generation**

Emit Markdown with this fixed order: purpose → workflow → operator preflight (`npm run penpot:check`) → checkpoint policy → screen brief → implementation rules → completion output. The handoff tells the AI assistant to use upstream `penpot-ai-kit`, inspect existing tokens/components first, propose direction before meaningful canvas changes, build section-by-section, run design-quality/accessibility review, then request visual approval.

- [ ] **Step 4: Implement deterministic manifest**

Use Node `createHash('sha256')` over canonical UTF-8 config JSON and brief Markdown. Sort object keys before serialization. Include only stable relative input paths such as `design-agent/config.json` and `design-agent/briefs/b2c-home.md`.

- [ ] **Step 5: Run tests**

Run: `npm test -- --run agent/design-control/test/handoff.test.ts agent/design-control/test/runManifest.test.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add agent/design-control
git commit -m "feat: generate Penpot AI Kit handoff manifests"
```

---

### Task 3: Offline design-control CLI and npm scripts

**Files:**
- Create: `agent/design-control/src/cli.ts`
- Create: `agent/design-control/test/cli.test.ts`
- Modify: `package.json`
- Modify: `tsconfig.json`

**Interfaces:**
- `npm run design:validate`
- `npm run design:brief -- --screen b2c-home`
- `npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json`

- [ ] **Step 1: Write failing CLI tests**

Test that `validate` returns success, `brief` writes handoff text to stdout, missing screen exits non-zero, and `run-manifest` creates stable JSON under a temporary output path.

- [ ] **Step 2: Run tests and observe failure**

Run: `npm test -- --run agent/design-control/test/cli.test.ts`
Expected: FAIL because CLI does not exist.

- [ ] **Step 3: Implement CLI**

Supported commands are exactly `validate`, `brief`, `run-manifest`. Parse `--screen` and `--out`; reject unknown flags. Create output directories recursively. `validate` prints compact JSON `{\"valid\":true,\"briefs\":[\"b2c-home\"]}`.

- [ ] **Step 4: Wire scripts and TypeScript include**

Add:

```json
"design:validate":"tsx agent/design-control/src/cli.ts validate",
"design:brief":"tsx agent/design-control/src/cli.ts brief",
"design:run-manifest":"tsx agent/design-control/src/cli.ts run-manifest"
```

Extend `tsconfig.json` include with `agent/design-control/src/**/*.ts` and `agent/design-control/test/**/*.ts`.

- [ ] **Step 5: Run unit/type checks**

Run: `npm test -- --run agent/design-control/test/cli.test.ts && npm run typecheck`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add package.json tsconfig.json agent/design-control
git commit -m "feat: add design control CLI"
```

---

### Task 4: Operator documentation and renderer status

**Files:**
- Create: `design-agent/README.md`
- Modify: `README.md`

**Interfaces:**
- Preferred flow is explicitly Product brief → `design:validate` → `design:brief` → `penpot:check` → upstream Penpot AI Kit + MCP → quality/a11y review → visual approval → DESIGN.md/tokens → Codex.

- [ ] **Step 1: Document the operator workflow**

Include Windows Command Prompt commands:

```cmd
npm install
npm run design:validate
npm run design:brief -- --screen b2c-home
npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json
npm run penpot:check
```

State that the generated handoff is pasted/provided to an MCP-capable assistant with Penpot AI Kit installed and the target Penpot file open/connected.

- [ ] **Step 2: Mark the old renderer experimental**

README must say the repository's direct visual renderer is retained for experimentation/backwards compatibility and is **not** the preferred screen-design path. Do not remove existing `penpot:*` commands.

- [ ] **Step 3: Commit**

```bash
git add README.md design-agent/README.md
git commit -m "docs: document Penpot AI Kit design workflow"
```

---

### Task 5: CI design-agent contract

**Files:**
- Modify: `.github/workflows/design-contract.yml`

**Interfaces:**
- CI runs `npm run design:validate` and generates a deterministic `artifacts/design-run.json` without network access or Penpot credentials.

- [ ] **Step 1: Extend CI**

After typecheck, add:

```yaml
      - run: npm run design:validate
      - run: npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json
```

Upload `artifacts/design-run.json` together with the existing Penpot dry-run plan.

- [ ] **Step 2: Run the complete local contract**

Run:

```bash
npm test -- --run
npm run typecheck
npm run validate
npm run design:validate
npm run design:run-manifest -- --screen b2c-home --out artifacts/design-run.json
npm run sync:dry -- --out artifacts/penpot-plan.json
```

Expected: all commands exit 0; generated manifest contains no MCP URL/key and is identical across two consecutive runs.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/design-contract.yml
git commit -m "ci: validate design agent contract"
```

---

## Self-review

- Spec coverage: config, template, production Home brief, validation, self-contained handoff, deterministic run manifest, README workflow, CI, existing MCP preflight and legacy renderer status are all mapped to tasks.
- No secrets are required or stored.
- No live Penpot mutation is introduced.
- `penpot-export`, Codex app generation, full B2B and renderer removal remain outside this wave per the spec.
