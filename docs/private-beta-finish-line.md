# Salty Pickle Private Beta Finish Line

## Goal

Ship a private beta on Railway and Vercel platform domains. The launch promise is
Strava login, AI training plan generation, dashboard/plan viewing, and optional
phone home-screen install through PWA support.

## Beta Scope

- Strava OAuth is the primary signup/login path.
- AI plan generation is required and depends on `OPENAI_API_KEY`.
- Google Calendar and Whoop are optional integrations during beta.
- Custom domains and native App Store packaging are deferred.

## Deployment Wiring

- Railway backend uses the repository `Dockerfile`, Postgres, Redis, `/live`
  healthcheck, and `alembic upgrade head` release command.
- Vercel frontend uses project root `frontend`, build command `npm run build`,
  and output directory `dist`.
- Use generated platform domains for beta:
  - Set Vercel `VITE_API_BASE_URL` to the Railway API origin.
  - Set Railway `FRONTEND_BASE_URL` and `FRONTEND_URL` to the Vercel app origin.
  - Set Railway `ALLOWED_ORIGINS` to the Vercel app origin if needed.
  - Configure Strava callback as `<railway-api-origin>/auth/strava/callback`.

## Acceptance Smoke

Run:

```bash
scripts/smoke_public_release.sh --api-base <railway-url> --app-base <vercel-url>
```

Then manually verify:

- `/login` starts Strava OAuth.
- Strava callback stores the session and redirects to `/create`.
- A beta user can generate an AI plan.
- Dashboard and plan editor render without fatal API or console errors.
- The Vercel app can be added to a phone home screen.

## Post-Beta Integrations

Garmin, Oura Ring, and Apple Health are post-beta work. Treat them as provider
data-ingestion projects, not just new buttons:

- Garmin: activity and training data.
- Oura Ring: sleep, readiness, and recovery signals.
- Apple Health: iPhone and Apple Watch workout/health data.

The follow-up design should define normalized storage, sync visibility,
duplicate handling, and provider precedence when multiple sources report the
same workout or recovery signal.
