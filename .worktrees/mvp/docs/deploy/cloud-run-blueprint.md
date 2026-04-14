# Cloud Run Blueprint (Consolidated Path)

Use this path when you want one cloud provider for API runtime + managed data.

## Topology

- Cloud Run service: `salty-pickle-api` (`api.yourdomain.com`)
- Cloud SQL (Postgres)
- Memorystore (Redis)
- Optional second Cloud Run service for scheduler worker

## 1) Provision Managed Services

1. Create Cloud SQL Postgres instance and database.
2. Create Memorystore (Redis) in the same region; use a [Serverless VPC Access connector](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access) so Cloud Run can reach private Redis.
3. Grant the Cloud Run runtime service account Cloud SQL Client (and Secret Manager access if you mount secrets).

## 2) Deploy API Service

Build/push image and deploy:

```bash
gcloud run deploy salty-pickle-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DEBUG=false,ENABLE_SCHEDULER=false
```

Then set secret/env values:

- `DATABASE_URL` (Cloud SQL connection URL)
- `REDIS_URL`
- `SECRET_KEY`
- OAuth client IDs/secrets
- `APP_PUBLIC_URL`, `API_PUBLIC_URL`, `ALLOWED_ORIGINS`, `FRONTEND_BASE_URL`
- provider callback URLs pointing to `api.yourdomain.com`

## 3) Optional Scheduler Worker

Deploy second service from same image with scheduler enabled:

- web service: `ENABLE_SCHEDULER=false`
- worker service: `ENABLE_SCHEDULER=true`

This avoids duplicate job execution from scaled web instances.

## 4) Domain Mapping

1. Map `api.yourdomain.com` to Cloud Run service.
2. Keep Lovable frontend on `app.yourdomain.com`.
3. Ensure HTTPS certificates are active before OAuth testing.

## 5) Migration Checklist (From Fast Track)

| Step | Action |
|------|--------|
| 1 | Keep Lovable/Vercel frontend domain and `ALLOWED_ORIGINS` entries unchanged unless you also change the app URL. |
| 2 | Deploy API to Cloud Run; assign `api.yourdomain.com` (or a new API hostname). |
| 3 | Update frontend `VITE_API_BASE_URL` / `VITE_PUBLIC_API_URL` to the Cloud Run URL. |
| 4 | Update Strava, Google, and Whoop redirect URIs to the new API origin (`docs/deploy/oauth-provider-setup.md`). |
| 5 | Migrate Postgres data (dump/restore or replication) into Cloud SQL; update `DATABASE_URL`. |
| 6 | Point Redis clients to Memorystore; update `REDIS_URL`. |
| 7 | Store `SECRET_KEY` and OAuth secrets in Secret Manager; reference from Cloud Run. |
| 8 | Run `alembic upgrade head` against Cloud SQL. |
| 9 | Run `./scripts/smoke_public_release.sh --api-base https://api.yourdomain.com --app-base https://app.yourdomain.com`. |
| 10 | Decommission old API service after traffic cutover. |

## 6) Validation Checklist

- `GET /live` returns alive
- `GET /healthz` confirms DB connectivity
- OAuth callback validates redirect host against allowed origins (`GET /auth/provider-callbacks` for visibility)
- Plan generation and calendar sync complete successfully
- Worker service (if used) runs with `ENABLE_SCHEDULER=true` only; web service has `ENABLE_SCHEDULER=false`
