# Launch Checklist

## Pre-Launch

- [ ] Secrets rotated and production values set in Railway.
- [ ] Vercel frontend environment variables set for Production and Preview.
- [ ] Railway Postgres and Redis attached to the backend service.
- [ ] DNS configured for app and API domains.
- [ ] `ALLOWED_ORIGINS`, `FRONTEND_URL`, and `FRONTEND_BASE_URL` match deployed frontend origins.
- [ ] Sentry receives backend and frontend test events.
- [ ] Uptime monitor active against `/healthz`.
- [ ] CI passing on `main`.
- [ ] Branch protection enabled for `main`.
- [ ] Rate limits tested for general, auth, and feedback endpoints.
- [ ] `/terms` and `/privacy` routes exist.
- [ ] Feedback endpoint and button tested.
- [ ] PostHog pageviews arriving, if `VITE_POSTHOG_KEY` is configured.
- [ ] OAuth provider callback URLs match production API domain.

## Launch Day

- [ ] Merge release branch to `main`.
- [ ] Confirm Railway deployment succeeds.
- [ ] Confirm Vercel deployment succeeds.
- [ ] Smoke test app reachability.
- [ ] Smoke test signup/login or bootstrap auth path.
- [ ] Smoke test Strava OAuth authorize redirect.
- [ ] Smoke test core training plan flow.
- [ ] Watch Sentry, Railway logs, Vercel logs, and uptime monitor for the first hour.

## Post-Launch

- [ ] Check feedback daily for the first week.
- [ ] Triage Sentry daily for the first week.
- [ ] Review Railway resource usage after real traffic.
- [ ] Review PostHog funnels/pageviews after real traffic.
- [ ] Replace placeholder legal copy before broad public launch.
