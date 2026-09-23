# Reuse-First Policy

For every capability resolve in this order:
1. Existing client implementation
2. Existing PinCommerce/Agency capability
3. Existing approved UI/component/module
4. Existing approved open-source system/plugin
5. Configuration of an existing solution
6. Extension of an existing solution
7. Custom implementation

Every provider decision must record:
- capability
- selected provider/module
- license/operational review status
- integration boundary
- extension points
- replacement strategy

Preferred starting providers are examples, not hard requirements:
Medusa (commerce), Mercur (marketplace), Tryton (ERP), Chatwoot (support), Meilisearch (search), Activepieces/Windmill (automation), PostgreSQL/Supabase (data), NATS/RabbitMQ (messaging), Valkey (cache), PostHog/GA4 (analytics), Superset/Metabase (BI).

## UI/UX reuse decisions

UI reuse decisions apply the same hierarchy at component level. A broad open-source/reference pool may be evaluated, but production dependencies are activated only when a governed design-selection record shows functional fit and the component remains behind PinCommerce shared primitives. Icon family, motion stack and theme preset are selected once per governed surface/product rather than mixed ad hoc.
