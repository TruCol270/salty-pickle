# Rollback

Use rollback when a release causes user-visible breakage, data corruption risk,
or sustained operational alerts.

## Vercel Frontend

1. Open the Vercel project.
2. Go to Deployments.
3. Pick the last known-good deployment.
4. Choose Promote to Production.
5. Smoke test `app.example.com`.

## Railway Backend

1. Open the Railway backend service.
2. Go to Deployments.
3. Select the last known-good deployment.
4. Redeploy the previous deployment.
5. Smoke test:

```bash
curl -fsS https://api.example.com/live
curl -fsS https://api.example.com/healthz
```

## Database Migrations

Prefer a forward fix migration after a migration has reached production.

Emergency options:

1. Stop write traffic if data integrity is at risk.
2. Restore the pre-deploy Postgres backup to a fresh database.
3. Point Railway `DATABASE_URL` at the restored database.
4. Redeploy the last known-good backend.
5. Validate core flows before reopening traffic.

Use Alembic downgrade only when the downgrade path has been rehearsed against a
copy of production data.

## Communication

- Owner: assign release lead before launch.
- Internal status: post in the team channel.
- User status: update the public status/support channel if user impact is real.
- After resolution: record cause, rollback decision, and follow-up fix.
