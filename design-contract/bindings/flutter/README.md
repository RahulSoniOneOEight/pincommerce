# Flutter Binding

Maps framework-independent Design Contract roles and component specifications into `agency_flutter_ui`.

Rules:
- semantic tokens only in application-facing widgets
- Material/Cupertino/shadcn-style widgets may be wrapped behind shared primitives
- Widgetbook stories are required for reusable primitives/patterns
- visual changes require golden coverage for critical states

Approved selection flow:
- default primitive candidate: shadcn_flutter, wrapped by agency_flutter_ui
- dense data: data_table_2
- complex forms: flutter_form_builder
- analytics: fl_chart
- remote commerce imagery: cached_network_image
- rails/carousels: carousel_slider
- default icon family: Iconoir; Phosphor/Lucide/Material Symbols require selection evidence
- default motion: flutter_animate/native Flutter; Rive/Lottie only where justified

Selection must originate from `experience/design/selection.yaml`; applications must not import a new design system merely by preference.
