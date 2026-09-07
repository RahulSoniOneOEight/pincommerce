# PinCommerce B2C Home Design Brief

Screen: b2c-home
Workflow: brief-to-screen
Viewport: 390x844
Theme: theme-b-blue

## Context
- Product & audience: PinCommerce B2C mobile commerce for customers buying construction, plumbing, electrical, sanitary, hardware and agriculture products.
- Platform: mobile-first 390×844 viewport.
- Brand mood: premium modern commerce, deep blue and white, restrained amber/gold accents, crisp hierarchy, subtle technical/watermark motifs only where they add polish.
- Reference direction: use the shared B2C Make home as the structural and merchandising reference. Keep its strong commerce density and section hierarchy, but adapt it to the PinCommerce Theme B system rather than copying its green palette.

## Objective
- Design the B2C Home screen so a customer can quickly search, browse categories/brands, discover promotions and products, and move into shopping with confidence.

## Inputs
- Required sections, top to bottom: branded header; search; strong commerce hero inspired by the Make home; category shortcuts; Top Brands; Flash Deals; Top Rated Products; bottom navigation.
- Category shortcuts should cover six useful commerce categories, including Plumbing, Electrical, Sanitary, Hardware/Tools and Agriculture plus one additional relevant category.
- Flash Deals should feel time-sensitive and product-led, with clear price/discount hierarchy and useful add/cart affordances.
- Top Rated Products should be visually distinct enough to scan as a second merchandising block rather than a repetition of Flash Deals.
- Existing tokens/components: inspect and reuse the PinCommerce semantic tokens, product-card patterns, search, header, chips/badges and bottom navigation before inventing new primitives.
- Visual reference guidance: take the Make reference's merchandising hierarchy, richness, section rhythm and category/brand/deal structure. Ignore its exact colors and any desktop-only spacing assumptions.

## Constraints
- Use Penpot-native editable shapes, components and tokens; do not flatten the screen into an image.
- Reuse existing components where suitable; instantiate rather than redraw.
- Bind colors, spacing, radius and typography to semantic design-system values; do not create an ad-hoc parallel color system.
- Theme B: deep navy/royal blue primary, white/light blue-grey surfaces, muted amber/gold used sparingly, soft grey-blue borders, minimal diffuse shadows and refined medium radii.
- Use a consistent 4px spacing rhythm.
- Keep watermark/geometric decoration subtle, approximately 2–4% opacity, and limit it to premium surfaces such as the hero.
- Keep touch targets appropriate for mobile use and preserve legible text at 390×844.
- Build section-by-section and pause for direction approval before meaningful canvas changes.

## Acceptance Criteria
- The screen visibly contains: branded header, search, commerce hero, 6 category shortcuts, Top Brands, Flash Deals, Top Rated Products and bottom navigation.
- The hierarchy should make search, hero offer, categories and product discovery immediately understandable within the first viewport.
- One primary commerce action should be visually dominant at any moment; secondary actions should not compete with it.
- Normal text contrast should target at least 4.5:1; large text and UI elements at least 3:1 where applicable.
- Product prices, discounts and calls-to-action should be scannable without zooming.
- Spacing should follow the 4px system with no arbitrary off-grid gaps.
- Output must remain fully editable in Penpot and reuse the active design system where possible.
- Run Penpot AI Kit design-quality review and accessibility review before presenting the screen for visual approval.
- Do not consider the screen approved until the user visually reviews the rendered Penpot result.
