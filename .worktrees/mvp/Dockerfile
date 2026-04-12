# --- Python deps ---
FROM python:3.11-slim AS py-builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Frontend build ---
FROM node:20-slim AS fe-builder

WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# --- Runtime ---
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=py-builder /install /usr/local
COPY --from=fe-builder /fe/dist ./static

COPY app ./app
COPY alembic.ini .
COPY worker_main.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8000
EXPOSE 8000

# Shell only for ${PORT}; `exec` replaces sh so uvicorn is PID 1 and receives SIGTERM.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
