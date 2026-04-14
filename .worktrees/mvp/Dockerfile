# --- Python deps ---
# Wheels-only: skip apt (gcc/libpq-dev) to avoid flaky remote builders; deps ship manylinux wheels.
FROM python:3.11-slim-bookworm AS py-builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 \
    --prefix=/install -r requirements.txt

# --- Frontend build ---
FROM node:20-bookworm-slim AS fe-builder

WORKDIR /fe
# Install devDependencies (Vite, TypeScript) even when the platform sets NODE_ENV=production during build.
ENV NODE_ENV=development
ENV NODE_OPTIONS=--max-old-space-size=8192
ENV CI=false
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV NODE_ENV=production
RUN npm run build

# --- Runtime ---
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=py-builder /install /usr/local
COPY app ./app
COPY --from=fe-builder /fe/dist ./app/static
COPY alembic.ini .
COPY worker_main.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

# Apply DB schema then start API. Fails fast if DATABASE_URL is wrong or migrations break.
# Shell only for ${PORT}; `exec` replaces sh so uvicorn is PID 1 and receives SIGTERM.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
