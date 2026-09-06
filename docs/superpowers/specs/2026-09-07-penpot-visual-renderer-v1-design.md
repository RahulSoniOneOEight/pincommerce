# Penpot Visual Renderer v1 Design

## Goal

Turn the existing GitHub-driven Penpot sync from structural scaffolding into an editable, production-like Theme B mobile commerce design system and first-screen slice. The first slice covers reusable visual primitives plus B2C Home, Category, and Product screens, while preserving the existing managed-object registry, non-destructive behavior, and idempotent live sync.

## Scope

### In scope

- Theme B — Premium Blue only for this wave.
- Native Penpot rendering of reusable visual primitives.
- Hybrid asset strategy:
  - category imagery uses Penpot-native vector/icon geometry;
  - product imagery uses polished neutral product-image placeholders;
  - no network image dependency in v1.
- Core reusable component renderers:
  - header
  - search bar
  - category chip
  - brand chip
  - product card
  - price block
  - quantity control
  - button
  - bottom navigation
  - badge
  - category icon block
  - product image placeholder block
- B2C screens:
  - Home
  - Category
  - Product
- Deterministic GitHub desired-state definitions for visual structure.
- Live Penpot update of already-managed components/screens instead of duplicate creation.
- Read-before-write and explicit `--apply` write gate remain mandatory.
- Verification that a second identical sync yields zero creates and zero updates for supported objects.

### Out of scope

- Theme A visual rendering in this wave.
- Cart, checkout, confirmation, tracking, orders, login, signup, or B2B screen composition.
- Live prototype-link creation.
- External image search/downloads, stock photography, or remote asset hosting.
- Direct `.penpot` archive manipulation.
- Auto-delete or destructive cleanup.
- Bidirectional Penpot → GitHub synchronization.

## Existing system constraints

The current live sync already manages pages, token sets, components, screens, and prototype-route intents through stable `repoId` identities stored in `pincommerce.managed.v1` plugin data. The current writer creates minimal boards/text placeholders for components/screens and real color tokens for token sets. This renderer must extend those same managed identities rather than introduce a second registry.

Current visual component IDs already exist in `design-system/components/catalog.json`, and Home/Category/Product already reference the correct component IDs in `screens/b2c/screens.json`. The renderer therefore enriches existing desired objects rather than replacing the overall domain model.

## Recommended architecture

Use a declarative renderer layer between repository manifests and Penpot MCP execution:

```text
GitHub manifests + visual definitions
              ↓
       Visual render model
              ↓
      Penpot render compiler
              ↓
   Penpot MCP execute_code
              ↓
 native Penpot shapes/components/screens
              ↓
 pincommerce.managed.v1 registry
```

### 1. Visual definitions

Add repository-owned visual definition files that describe composition without embedding raw Penpot scripting into manifests.

Suggested structure:

```text
design-system/
  visual/
    theme-b.json
    components.json
    assets.json
screens/
  b2c/
    visual-v1.json
```

`theme-b.json` provides resolved Theme B rendering values such as colors, typography roles, spacing, radii, shadows, and selected watermark treatment. It should reference or derive from the existing Theme B token source rather than duplicate canonical token values unnecessarily.

`components.json` defines the child structure for the v1 reusable components. Each component definition contains a stable component id, frame size or layout constraints, visual roles, and children such as text, rectangle, icon, badge, or nested component slot.

`assets.json` defines a small closed set of generated vector/icon recipes and product-placeholder recipes. These remain deterministic and offline.

`visual-v1.json` defines the Home/Category/Product section order and sample content used for design rendering.

### 2. Visual render model

Introduce a typed intermediate model so repository JSON and Penpot scripting are decoupled.

Conceptual node types:

```ts
type RenderNode =
  | FrameNode
  | RectNode
  | TextNode
  | IconNode
  | ComponentInstanceNode;
```

Each render node has stable local identity, geometry/layout properties, style roles, and optional content. The model should be deliberately small; v1 only supports primitives required for the first three screens.

### 3. Penpot render compiler

The compiler converts normalized visual definitions into controlled Penpot plugin API code used through the existing `execute_code` gateway.

Responsibilities:

- resolve Theme B style roles to concrete token values;
- create/update child shapes under the already-managed root object;
- use deterministic generated names such as `PCV1::<repoId>::<nodeId>`;
- rebuild only the managed visual subtree of that object;
- avoid touching unrelated user-created shapes;
- create true Penpot library components for component definitions where the current plugin API safely allows it;
- compose screen boards using either component instances where supported or deterministic managed render groups when instance APIs are not safely available.

The compiler must keep Penpot-specific code isolated from visual manifests.

### 4. Managed visual subtree

Each managed component/screen root keeps its current `repoId` registration. Visual children created by v1 receive deterministic names and are considered owned by the renderer only when they are inside that managed root and carry the renderer naming convention.

Update behavior:

1. inspect the current managed root;
2. identify the renderer-owned child subtree;
3. replace/reconcile only renderer-owned children;
4. leave unrelated child shapes and all unrelated Penpot objects untouched;
5. update registry payload/version after successful rendering.

No root deletion is allowed.

## Theme B visual direction

### Color and surface hierarchy

- Primary: deep navy / royal blue from existing Theme B tokens.
- Background: white / very light blue-grey.
- Primary text: near-black navy.
- Secondary text: muted blue-grey.
- Borders: soft grey-blue.
- Accent: restrained amber/gold only for selected highlight states.
- CTA: high-contrast blue with white foreground.

### Shape language

- Mobile canvas: 390 × 844.
- Medium refined radii.
- Minimal diffuse shadow treatment.
- 16–20 px default side padding depending on component.
- Tighter, premium typography hierarchy.

### Watermark treatment

Use the approved low-opacity 2–4% geometric treatment only in selected areas:

- Home hero banner.
- Product hero/media area where it does not reduce clarity.
- Optional category section header treatment.

Motifs are deterministic geometric recipes such as blueprint grid, technical lines, blocks, or monogram geometry. No bitmap watermark is required.

## Hybrid asset strategy

### Category icons

Category icons are rendered from simple native/vector geometry so they remain editable in Penpot. Initial categories should cover the commerce context already established for the project, including plumbing, electrical, sanitary, paints/construction, hardware/tools, and agriculture.

The icon style is consistent: rounded line/block geometry, compact bounding box, Theme B primary/accent roles, no external dependency.

### Product imagery

Product cards and Product screen use polished neutral placeholders rather than stock images. Placeholder recipe:

- light blue-grey media surface;
- centered simplified product silhouette or geometric object;
- subtle depth/highlight treatment;
- optional small category label;
- no URL or remote fetch.

The placeholder is a replaceable media slot, so later real product images can be swapped without changing component structure.

## Component designs

### Header

Variants: `home`, `detail`.

Home contains brand/wordmark treatment, location or delivery cue, and utility icon slot. Detail contains back affordance, title, and optional utility icon.

### Search bar

Rounded search field with search icon, hint text, and subtle surface/border. Active variant may use stronger primary border treatment.

### Category chip

Compact icon + label or text-only chip depending on context. Selected state uses primary tint and stronger text/icon.

### Brand chip

Compact rounded chip with neutral surface; selected state uses primary outline/tint.

### Product card

Core structure:

```text
media placeholder
badge/discount
brand
product name
price + original price
optional rating/info
CTA or quantity affordance
```

B2C variant only needs to be visually rendered in v1, while preserving the catalog's B2B variant definition for later work.

### Price block

Strong current price, lighter struck-through original price, restrained discount treatment.

### Quantity control

Minus / current quantity / plus in a compact bordered control.

### Button

Primary and secondary variants rendered; ghost may remain structurally supported but does not need to appear in the first three screens.

### Bottom navigation

Five-item mobile navigation aligned to the current commerce IA: Home, Browse, Orders, Cart, Login/Profile. Active item uses primary blue; inactive items use muted text/icon.

### Badge

Discount/info/status visual primitives. First slice primarily uses discount and info.

## Screen compositions

### B2C Home

Order:

1. Premium blue home header.
2. Search bar.
3. Hero banner with subtle geometric watermark and restrained promotional copy.
4. Category icon row/grid.
5. Top brands row.
6. Flash deals section using reusable product cards.
7. Top rated/products section using reusable product cards.
8. Bottom navigation.

The design should feel content-rich but not visually crowded. Hero and cards should establish hierarchy without excessive decoration.

### B2C Category

Order:

1. Detail/category header.
2. Category or section title.
3. Category/brand filter chips.
4. Product result count/sort cue.
5. Two-column product card grid or vertically efficient equivalent appropriate to 390 px width.
6. Bottom navigation.

### B2C Product

Order:

1. Detail header.
2. Large media placeholder/gallery region.
3. Brand and product name.
4. Rating/info badge row.
5. Price block.
6. Short commerce information such as delivery/availability.
7. Quantity control.
8. Primary add-to-cart/buy CTA.
9. Bottom navigation.

## Data and sample content

The renderer uses deterministic sample content committed to GitHub solely for the design system demonstration. Content should reflect the existing building-materials / retail commerce context without pretending to be live catalog data.

Example categories and product names may be realistic but generic. No scraped brand assets or copyrighted product photography should be embedded.

## Sync and diff semantics

The existing high-level operation planner remains unchanged in spirit. A managed component/screen becomes `update` when its visual render definition/version changes.

Add a visual revision/fingerprint to relevant operation payloads so the existing diff planner can detect meaningful visual-definition changes without inspecting every Penpot shape remotely.

After successful render, the registry stores the applied visual revision and normalized visual payload reference.

Expected workflow:

```text
npm run penpot:plan
→ visual component/screen updates appear

npm run penpot:sync -- --apply
→ updates only existing managed roots

npm run penpot:verify
→ verifies registry + managed root presence/revision

npm run penpot:plan
→ create=0, update=0 for supported desired objects
```

## Error handling and safety

- Existing target-file guard remains mandatory.
- Live writes still require `--apply`.
- If a managed root referenced by the registry no longer exists, report a write/read consistency error rather than silently creating a duplicate during update.
- Unsupported Penpot API operations must be surfaced explicitly, not approximated destructively.
- If true component-instance composition is unavailable or unreliable in the current Penpot plugin API, screen composition may use deterministic renderer-owned groups while preserving library components separately. This fallback must be reported in code/tests and must not block the three-screen visual slice.
- No renderer action may delete unrelated shapes or unmanaged roots.
- Prototype links remain unsupported and untouched.

## Testing strategy

### Unit tests

- visual schema validation;
- Theme B role resolution;
- deterministic render-node compilation;
- stable child naming;
- hybrid icon/placeholder recipe generation;
- visual fingerprint stability;
- changed visual definition causes update;
- identical visual definition causes unchanged;
- renderer never emits root delete operations.

### Gateway/compiler tests with fake MCP transport

- create/update generated code targets the correct managed root;
- renderer-owned subtree is scoped by deterministic naming convention;
- unrelated children are preserved;
- missing managed root fails safely;
- repeated identical render becomes idempotent in registry state.

### CLI regression

Existing `check`, `plan`, `sync -- --apply`, and `verify` safety tests continue to pass without live credentials.

### Live acceptance

On the connected `piv1` Penpot file:

1. `penpot:check` succeeds.
2. `penpot:plan` reports updates only for objects enriched by Visual Renderer v1.
3. `penpot:sync -- --apply` succeeds without duplicate roots.
4. Home, Category, Product and reusable core components are visually inspectable and editable in Penpot.
5. `penpot:verify` succeeds.
6. second `penpot:plan` reports zero creates and zero updates for supported objects.

## Success criteria

Visual Renderer v1 is complete when:

- Theme B is visibly applied to native Penpot shapes.
- Header, Search, Category Chip, Brand Chip, Product Card, Price Block, Quantity Control, Button, Bottom Nav, Badge, category icon block, and product placeholder block are represented by reusable/native Penpot structures.
- B2C Home, Category, and Product are fully composed at 390 × 844 and visually coherent.
- Existing managed roots are updated rather than duplicated.
- User-created/unmanaged objects remain untouched.
- No network imagery is required.
- Live verification passes.
- A second identical plan returns `create=0` and `update=0` for supported managed objects.

## Follow-on waves

After this slice is visually approved in Penpot:

1. Theme B: Cart → Checkout → Confirmation → Tracking → Orders → Login/Signup.
2. B2B screen composition and B2B component variants.
3. Theme A token-driven rendering against the same component hierarchy.
4. Prototype/interactions layer when a safe Penpot API path is available or via a documented manual interaction pass.
