# Web Binding

Maps framework-independent Design Contract roles and component specifications into `agency_web_ui`.

Rules:
- semantic CSS variables/tokens
- reusable primitives before page-local styling
- Storybook coverage for reusable primitives/patterns
- responsive, keyboard and accessibility states are contract requirements

Approved selection flow:
- default owned component source: shadcn/ui with Base UI primitives where suitable
- Radix/React Aria: compatibility or accessibility-specialized candidates
- dense data: TanStack Table
- server state: TanStack Query
- forms: React Hook Form
- analytics: Recharts
- rails/carousels: Embla
- default icon family: Iconoir; Lucide/Phosphor/Material Symbols require selection evidence
- default motion: Motion for React or CSS/WAAPI; GSAP only for justified advanced timelines

Selection must originate from `experience/design/selection.yaml`; applications must not add a competing design system merely by preference.
