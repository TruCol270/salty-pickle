# Launch Checklist

## Pre-Launch

- [ ] Current private-beta stabilization fixes committed and CI passing.
- [ ] Railway and Vercel generated HTTPS platform domains selected for beta.
- [ ] Secrets rotated and production values set in Railway.
- [ ] Vercel frontend environment variables set for Production and Preview.
- [ ] Railway Postgres and Redis attached to the backend service.
- [ ] DNS intentionally deferred; platform domains are used for private beta.
- [ ] `ALLOWED_ORIGINS`, `FRONTEND_URL`, and `FRONTEND_BASE_URL` match deployed frontend origins.
- [ ] `VITE_API_BASE_URL` points to the deployed Railway API origin.
- [ ] `OPENAI_API_KEY` is configured and has quota for beta testers.
- [ ] Sentry receives backend and frontend test events.
- [ ] Uptime monitor active against `/healthz`.
- [ ] CI passing on `main`.
- [ ] Branch protection enabled for `main`.
- [ ] Rate limits tested for general, auth, and feedback endpoints.
- [ ] `/terms` and `/privacy` routes exist.
- [ ] Feedback endpoint and button tested.
- [ ] PostHog pageviews arriving, if `VITE_POSTHOG_KEY` is configured.
- [ ] OAuth provider callback URLs match production API domain.
- [ ] PWA manifest, icon, and service worker are present in the deployed frontend.

## Launch Day

- [ ] Merge release branch to `main`.
- [ ] Confirm Railway deployment succeeds.
- [ ] Confirm Vercel deployment succeeds.
- [ ] Smoke test app reachability.
- [ ] Smoke test signup/login or bootstrap auth path.
- [ ] Smoke test Strava OAuth authorize redirect.
- [ ] Smoke test core training plan flow.
- [ ] Smoke test Add to Home Screen on at least one iPhone or Android device.
- [ ] Watch Sentry, Railway logs, Vercel logs, and uptime monitor for the first hour.

## Post-Launch

- [ ] Check feedback daily for the first week.
- [ ] Triage Sentry daily for the first week.
- [ ] Review Railway resource usage after real traffic.
- [ ] Review PostHog funnels/pageviews after real traffic.
- [ ] Replace placeholder legal copy before broad public launch.
- [ ] Scope Garmin, Oura Ring, and Apple Health integrations from beta feedback.
