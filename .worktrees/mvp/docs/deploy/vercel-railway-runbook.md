# Fast Track Runbook: Vercel + Railway (or Render)

This is the recommended fastest path to launch.

## Architecture

- Frontend: Lovable → publish to Vercel (or GitHub integration) on `app.yourdomain.com`
- API: Railway **or** Render (Docker) on `api.yourdomain.com`
- Data: managed Postgres + Redis from the same platform as the API

## 1A) Railway API Service

1. Create a Railway project and connect this repo.
2. Set the service root to `.worktrees/mvp` (or the directory that contains `Dockerfile` and `app/`).
3. Deploy using `Dockerfile` (`railway.toml` sets `healthcheckPath = "/live"`).
4. Add Postgres and Redis plugins.
5. Set env vars from `.env.production.example`:
   - `DATABASE_URL` (Railway Postgres internal URL)
   - `REDIS_URL` (Railway Redis internal URL)
   - all OAuth/client secrets
   - production URLs (`APP_PUBLIC_URL`, `API_PUBLIC_URL`, `FRONTEND_BASE_URL`, `ALLOWED_ORIGINS`)
6. Run migrations in Railway shell:
   - `alembic upgrade head`
7. Attach custom domain `api.yourdomain.com` and set public env vars to use `https://api.yourdomain.com`.

## 1B) Render API + worker (alternative)

`render.yaml` defines a **web** service and a **worker** (scheduler). Import the blueprint in the Render dashboard or use `render.yaml` from the repo root that contains it.

1. Create Postgres and Redis instances on Render; copy connection strings into both services.
2. Set the same env vars as Railway (see `.env.production.example`). Web service: `ENABLE_SCHEDULER=false`. Worker: `ENABLE_SCHEDULER=true`.
3. Run `alembic upgrade head` once (Render shell or one-off job) before relying on `/healthz`.
4. Map `api.yourdomain.com` to the web service.

## 2) Vercel/Lovable Frontend

1. In Lovable: connect GitHub and publish, or export and deploy the generated frontend to Vercel.
2. In Vercel project settings → Environment Variables:
   - `VITE_API_BASE_URL=https://api.yourdomain.com`
3. Redeploy so the build picks up the variable.
4. Map `app.yourdomain.com` to the Vercel project.
5. Add `https://app.yourdomain.com` (and any preview URLs you use) to API `ALLOWED_ORIGINS`.
6. Confirm “Connect Strava” opens `https://api.yourdomain.com/auth/strava/authorize?...` (see `frontend/src/lib/oauth.ts`).

## 3) Domain Mapping

1. Point DNS:
   - `app` CNAME -> Vercel target
   - `api` CNAME -> Railway target
2. Verify valid TLS on both hosts.

## 4) Provider OAuth Configuration

Set callbacks in provider dashboards:

- Strava: `https://api.yourdomain.com/auth/strava/callback`
- Google: `https://api.yourdomain.com/auth/google/callback`
- Whoop: `https://api.yourdomain.com/auth/whoop/callback`

## 5) Smoke Test

Use `scripts/smoke_public_release.sh`:

```bash
./scripts/smoke_public_release.sh \
  --api-base "https://api.yourdomain.com" \
  --app-base "https://app.yourdomain.com"
```

Then manually validate:

1. Open `https://app.yourdomain.com/login`
2. Click Connect Strava
3. Complete OAuth and confirm redirect back to app with session
4. Open integrations page and connect Google/Whoop (these use authenticated `POST /auth/*/authorize-url`)
5. Create plan and sync to calendar

## 6) Launch Gate

- `/live` returns 200
- `/healthz` returns ready with DB ok
- OAuth round-trip works for new and existing users
- API requests include bearer token after callback flow
