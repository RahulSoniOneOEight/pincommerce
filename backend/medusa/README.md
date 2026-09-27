# PinCommerce — Medusa backend

A real Medusa v2 (2.21.1) backend for the PinCommerce prototype's **commerce**
domain. Scaffolded with `create-medusa-app` (`--use-npm`), committed here so the
commerce core is reproducible. Third-party services (payment, logistics) remain
mocked per the repo's "mock in staging, real in prod" policy.

## Layout

- `apps/backend/` — the Medusa backend (`medusa-config.ts`, API, workflows,
  subscribers, seed scripts).
- `docker-compose.yml` — Postgres + Redis + Medusa.
- `Dockerfile` — builds the backend from source (Medusa publishes no prebuilt
  image).

## Run

```sh
docker compose up --build
```

On first boot the container runs migrations and seeds 50 demo products, then
serves the API on `http://localhost:9000`. The Flutter storefront points at it
via:

```sh
cd apps/prototype_app
flutter run \
  --dart-define=MEDUSA_BASE_URL=http://localhost:9000 \
  --dart-define=MEDUSA_PUBLISHABLE_KEY=<pk_...>
```

## Seed & bootstrap notes

- The committed `apps/backend/src/scripts/seed-demo-products.ts` creates demo
  **products** (deterministic handles, safe to re-run).
- A full bootstrap (region + sales channel + publishable API key + admin user,
  in **INR** to match `platform/prototype/baselines/medusa-standard-v1.yaml`)
  is the next step — it requires a live Postgres to verify, so it will land as a
  follow-up. Until then, run `npx medusa seed` / create the publishable key from
  the admin UI after boot.

## Requirements

- Docker Desktop (daemon must be running)
- Node 20.19+ (only needed to build outside Docker)
