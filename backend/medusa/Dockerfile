# Build the Medusa v2 backend. Medusa ships no prebuilt image, so this builds
# from the scaffolded backend source in this directory.
FROM node:20-alpine

WORKDIR /server

# Install dependencies first for better layer caching.
COPY package.json package-lock.json turbo.json ./
COPY apps/backend/package.json ./apps/backend/package.json
RUN npm install

COPY . .

WORKDIR /server/apps/backend

# Migrate, seed demo products (best-effort), then run the dev server.
CMD ["sh", "-c", "npx medusa db:migrate && (npx medusa exec ./src/scripts/seed-demo-products.ts || true) && npx medusa develop"]
