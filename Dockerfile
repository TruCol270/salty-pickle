# Build from repository root (Railway default) so COPY paths match clone layout.
# For deploys with service Root Directory = .worktrees/mvp, use that folder's Dockerfile instead.
#
# --- Python deps ---
# Wheels-only install: avoid apt (gcc/libpq-dev) — flaky on some remote builders and usually unnecessary
# for psycopg2-binary/asyncpg/cryptography on linux/amd64 and arm64.
FROM python:3.11-slim-bookworm AS py-builder

WORKDIR /build

COPY .worktrees/mvp/requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 \
    --prefix=/install -r requirements.txt

# --- Frontend build ---
FROM node:20-bookworm-slim AS fe-builder

WORKDIR /fe
# Install devDependencies (Vite, TypeScript) even when the platform sets NODE_ENV=production during build.
ENV NODE_ENV=development
# Vite/Rollup can OOM on small build VMs (common Railway failure for "npm run build").
ENV NODE_OPTIONS=--max-old-space-size=8192
ENV CI=false
COPY .worktrees/mvp/frontend/package.json .worktrees/mvp/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY .worktrees/mvp/frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV NODE_ENV=production
RUN npm run build

# --- Runtime ---
FROM python:3.11-slim-bookworm

WORKDIR /app

# No apt here: psycopg2-binary + asyncpg wheels bundle what they need for typical Linux targets.

COPY --from=py-builder /install /usr/local
COPY .worktrees/mvp/app ./app
# Colocate Vite dist with the package so Path(__file__).parent / "static" always resolves in the image.
COPY --from=fe-builder /fe/dist ./app/static
COPY .worktrees/mvp/alembic.ini .
COPY .worktrees/mvp/worker_main.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
