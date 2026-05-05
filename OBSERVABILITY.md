# Observability

Salty Pickle uses env-gated Sentry and structured backend logs. Local
development is quiet by default: leave DSNs blank unless you are testing
telemetry.

## Sentry

1. Create separate Sentry projects for the FastAPI backend and React frontend.
2. Set the backend DSN in Railway:
   - `SENTRY_DSN`
   - `ENVIRONMENT=production`
   - `RELEASE=<git-sha-or-release-name>`
3. Set the frontend DSN in Vercel:
   - `VITE_SENTRY_DSN`
   - `VITE_RELEASE=<git-sha-or-release-name>`
4. Redeploy both services.

Sentry initialization is skipped when the DSN is empty. Backend events scrub
authorization headers, cookies, tokens, secrets, passwords, API keys, and client
secrets before sending.

## Logs

Backend logs are JSON formatted through `structlog`. Configure verbosity with:

```text
LOG_LEVEL=INFO
```

Use `DEBUG` locally and `INFO` or `WARNING` in production. Request logs include
method, path, status code, and duration. Errors are logged with exception
context.

Access logs in:

- Railway: service dashboard -> Logs
- Vercel: project dashboard -> Logs

## Uptime Monitoring

Use a free monitor such as Better Stack, UptimeRobot, or Cronitor.

Recommended monitor:

- URL: `https://api.yourdomain.com/healthz`
- Interval: 5 minutes
- Expected status: `200`
- Alert route: owner email or Slack channel

Also keep a lightweight liveness monitor on `/live` if you want to separate
process availability from database readiness.

## Alert Triage

1. Check Sentry for the exception and release.
2. Check Railway logs for matching request IDs, paths, and timestamps.
3. Check Vercel logs for browser-side errors or failed API calls.
4. If customer impact is likely, follow [ROLLBACK.md](ROLLBACK.md).
