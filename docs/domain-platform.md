# Domain Platform & Integration Runtime

Part 3B introduces provider-neutral operational domains.

## Boundary model

Experience / business capability
→ canonical command/event
→ Integration Runtime
→ provider adapter
→ external system

Provider-specific models stay behind adapters.

## Initial providers

- Commerce: Medusa
- Marketplace: Mercur
- ERP: Tryton
- Search: Meilisearch
- Customer Support: Chatwoot
- Automation: Activepieces

These are default provider candidates selected by the Solution Contract, not architectural requirements.

## Integration guarantees

The runtime provides:
- canonical commands/events
- idempotency
- bounded retries
- delivery audit
- correlation IDs
- reconciliation records

The current transport is injectable for deterministic tests. Live HTTP/NATS/RabbitMQ transports are a later deployment binding and require environment credentials/configuration.

## Reference flow

order.confirmed
→ erp.create_sales_order
→ Tryton adapter
→ reconciliation: commerce-order-to-erp

Other supported adapter boundaries include product search indexing, support conversation creation, automation flow triggers and seller synchronization.


## Functional prototype rule

Phase C uses real core business runtimes, not mock commerce/ERP backends.

- Medusa is the standard commerce core when commerce is in scope.
- Mercur is the standard marketplace layer when marketplace/multi-vendor scope is active. Mercur extends Medusa.
- Tryton is the standard ERP core when ERP, warehouse or accounting scope is active.
- The client brief only overrides the affected baseline component; all unspecified behavior remains on the standard baseline.
- External providers such as Razorpay, Shiprocket and WhatsApp may use deterministic mock/sandbox bindings during prototype review.

The governed runtime record is `experience/prototype-core-runtime.yaml`. Client Review is blocked until every required core module is healthy with evidence and the linked demo dataset is ready.

See `docs/functional-prototype-runtime.md`.
