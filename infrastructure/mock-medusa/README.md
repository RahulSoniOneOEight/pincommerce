# Mock Medusa storefront server

A zero-dependency mock of the Medusa v2 **storefront** REST API, seeded with an
INR catalog. It serves the exact endpoints the PinCommerce Flutter storefront
uses, so you can run the app end-to-end without a real Medusa backend.

This mirrors the repo's **"mock in staging, real in prod"** policy. Use it for
prototyping and development; point the app at a real Medusa for production (see
below).

## Run

```sh
python infrastructure/mock-medusa/server.py --port 9000
```

Then run the Flutter app against it:

```sh
cd apps/prototype_app
flutter run \
  --dart-define=MEDUSA_BASE_URL=http://localhost:9000 \
  --dart-define=MEDUSA_PUBLISHABLE_KEY=mock
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | health check |
| GET | `/store/products` | list products (offset/limit) |
| GET | `/store/products/:id` | get a product |
| POST | `/store/carts` | create a cart |
| GET | `/store/carts/:id` | get a cart |
| POST | `/store/carts/:id/line-items` | add a line item |
| POST | `/store/carts/:id/line-items/:line_id` | update quantity |
| DELETE | `/store/carts/:id/line-items/:line_id` | remove a line item |
| POST | `/store/carts/:id` | set email / shipping address |
| POST | `/store/carts/:id/complete` | complete the cart into an order |

Amounts are in INR **paise** (minor units), matching Medusa's money model.

## Real Medusa (production path)

For production, run an actual Medusa v2 backend. The official, turnkey path is:

```sh
npx create-medusa-app@latest
```

This scaffolds a Medusa backend (and optionally a storefront) with a
`docker-compose` for Postgres/Redis, runs migrations, and seeds a default
catalog. Then:

1. Enable the storefront endpoints and create a **publishable API key**
   (region INR to match the baseline `platform/prototype/baselines/medusa-standard-v1.yaml`).
2. Point the Flutter app at it:

```sh
flutter run \
  --dart-define=MEDUSA_BASE_URL=https://your-medusa-backend \
  --dart-define=MEDUSA_PUBLISHABLE_KEY=pk_...
```

The Flutter client hits only `/store/*` endpoints, so any Medusa v2 backend with
the storefront API enabled and a publishable key is compatible.
