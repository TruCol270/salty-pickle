# Secrets Handling

This repository must not store real secrets in Git. Keep local values in `.env`,
`.env.local`, or `.env.*.local`; those files are ignored. Commit only example
templates with placeholders.

## Required Backend Variables

- `DATABASE_URL` - Postgres connection string. Railway can inject this from the
  Postgres plugin.
- `REDIS_URL` - Redis connection string. Railway can inject this from the Redis
  plugin.
- `SECRET_KEY` - JWT signing key and token-encryption key material. Generate a
  strong value per environment.
- `DEBUG` - Use `false` outside local development.
- `ENVIRONMENT`, `RELEASE`, `LOG_LEVEL` - Runtime metadata for logs and
  observability.
- `SENTRY_DSN` - Optional backend Sentry DSN.
- `APP_PUBLIC_URL` - Public frontend origin.
- `API_PUBLIC_URL` - Public API origin.
- `ALLOWED_ORIGINS` - Comma-separated browser origins allowed by CORS.
- `FRONTEND_URL` - Railway-friendly CORS helper, merged with `ALLOWED_ORIGINS`.
- `FRONTEND_BASE_URL` - Canonical frontend origin for OAuth fallback redirects.
- `RATE_LIMIT_GENERAL`, `RATE_LIMIT_AUTH`, `RATE_LIMIT_FEEDBACK` - API rate
  limit policies.
- `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REDIRECT_URI`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET`, `WHOOP_REDIRECT_URI`
- `OPENAI_API_KEY` - Backend-only AI plan generation key.

## Optional Backend Variables

- `ALGORITHM` - JWT algorithm, defaults to `HS256`.
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT lifetime, defaults to one week.
- `ENABLE_SCHEDULER` - Set `true` only on the worker service.
- `WORKER_SERVICE` - Set `true` on the worker service. `worker_main.py` also
  sets this automatically for worker process startup.
- `AUTH_BOOTSTRAP_KEY` - Ops-only bootstrap token for `POST /auth/token/bootstrap`.
  Leave unset in public production unless intentionally doing first-user setup.
- `GCP_PROJECT_ID`, `GCP_REGION` - Cloud deployment metadata when using GCP.
- `RAW_PAYLOAD_RETENTION_DAYS` - Provider raw-payload cleanup window.

## Frontend Variables

- `VITE_API_BASE_URL` - Public API base URL. Safe to expose because Vite embeds
  it in the browser bundle.
- `VITE_PUBLIC_API_URL` - Optional compatibility alias; ignored when
  `VITE_API_BASE_URL` is set.
- `VITE_SENTRY_DSN`, `VITE_RELEASE` - Optional frontend Sentry configuration.
- `VITE_POSTHOG_KEY`, `VITE_POSTHOG_HOST` - Optional frontend PostHog
  configuration if product analytics is wired in.

Do not put backend secrets in frontend variables. Any variable prefixed with
`VITE_` is public.

## Railway

Set backend variables in Railway service Variables, not in committed files.
Prefer plugin-provided `DATABASE_URL` and `REDIS_URL`. Configure web and worker
services separately:

- Web service: `ENABLE_SCHEDULER=false`, `WORKER_SERVICE=false`.
- Worker service: `ENABLE_SCHEDULER=true`, `WORKER_SERVICE=true`.

Keep `ALLOWED_ORIGINS`, `FRONTEND_URL`, and `FRONTEND_BASE_URL` aligned with the
actual Vercel/Lovable/custom frontend domains users open in the browser.

## Vercel

Set only frontend-safe variables in Vercel Project Settings:

- `VITE_API_BASE_URL=https://api.yourdomain.com`
- Optional: `VITE_PUBLIC_API_URL=https://api.yourdomain.com`

Never add OAuth client secrets, `OPENAI_API_KEY`, `SECRET_KEY`, database URLs,
Redis URLs, or bootstrap keys to Vercel frontend variables.

## Rotation

If a real secret is ever committed, revoke or rotate it at the provider before
removing it from Git. Add `SECRETS_TO_ROTATE.md` only when there are concrete
secrets that need rotation, and list the affected provider, variable name, and
commit/path evidence without repeating the secret value.
