# Lovable + FastAPI Integration

This project is configured so Lovable can act as the public frontend while FastAPI remains the source of truth for auth and business logic.

## 1) Required Environment Variables

Set these in your API host:

- `APP_PUBLIC_URL=https://app.yourdomain.com`
- `API_PUBLIC_URL=https://api.yourdomain.com`
- `ALLOWED_ORIGINS=https://app.yourdomain.com,https://staging.yourdomain.com`
- `FRONTEND_BASE_URL=https://app.yourdomain.com`
- `STRAVA_REDIRECT_URI=https://api.yourdomain.com/auth/strava/callback`
- `GOOGLE_REDIRECT_URI=https://api.yourdomain.com/auth/google/callback`
- `WHOOP_REDIRECT_URI=https://api.yourdomain.com/auth/whoop/callback`

`ALLOWED_ORIGINS` must list **every** browser origin you use: production app domain, Lovable publish URL, and any Vercel preview URL you use against this API. OAuth `redirect_url` is validated against the same allowlist (plus `FRONTEND_BASE_URL`). If a origin is missing, the API returns `400` for `redirect_url origin is not allowed`.

Set this in Lovable (Project → Environment / Secrets) or Vercel:

- `VITE_API_BASE_URL=https://api.yourdomain.com`

Optional alias (if your template already uses it):

- `VITE_PUBLIC_API_URL=https://api.yourdomain.com`

See `frontend/.env.example` in this repo.

## 2) OAuth Flow Contract

Start OAuth from frontend by sending users to:

- `GET /auth/strava/authorize?redirect_url=https://app.yourdomain.com/integrations`
- `POST /auth/google/authorize-url` with JSON body `{ "redirect_url": "https://app.yourdomain.com/integrations" }` and bearer auth
- `POST /auth/whoop/authorize-url` with JSON body `{ "redirect_url": "https://app.yourdomain.com/integrations" }` and bearer auth

Behavior:

1. `/auth/*/authorize` now redirects directly to provider OAuth.
2. Provider callback returns to `https://api.yourdomain.com/auth/*/callback`.
3. API mints JWT and redirects to `redirect_url` with `access_token` in URL fragment (`#access_token=...`).
4. Frontend stores token and removes it from URL.

## 3) Frontend Auth Session Wiring

Current frontend implementation supports:

- `access_token` in query string (`?access_token=...`) for backwards compatibility
- `access_token` in hash fragment (`#access_token=...`) for safer production callbacks
- automatic `Authorization: Bearer <token>` header on all API calls
- automatic logout + redirect to `/login` on `401`

Key files:

- `frontend/src/lib/env.ts` — `getApiBaseUrl()` (`VITE_API_BASE_URL` / `VITE_PUBLIC_API_URL`)
- `frontend/src/lib/authSession.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/lib/oauth.ts`

### Wiring a Lovable-generated React app

1. Add dependency: `axios` (or replicate interceptors with `fetch`).
2. Copy the files above (and keep import paths consistent), or merge `consumeAuthFromUrl` + `persistAuthSession` into your root layout.
3. Wrap your app with `AuthProvider` from `AuthContext.tsx` so `useEffect` runs once on load to capture OAuth return.
4. Ensure “Connect Strava” navigates to `buildOAuthAuthorizeUrl('strava', '/integrations')` (or your post-login path); that builds `GET {API}/auth/strava/authorize?redirect_url={currentOrigin}/integrations`.

## 4) Lovable Custom Code Notes

If your Lovable project uses custom JS for requests:

1. Read and store `access_token` from URL.
2. Strip token from URL via `history.replaceState`.
3. Attach token to API requests.

Pseudo flow:

```ts
const params = new URLSearchParams(window.location.search);
const token = params.get('access_token');
if (token) {
  sessionStorage.setItem('access_token', token);
  params.delete('access_token');
  history.replaceState({}, '', `${location.pathname}?${params.toString()}`);
}
```

Prefer the full `consumeAuthFromUrl` implementation in `authSession.ts`, which also reads hash fragments and matches the backend redirect format.

## 5) Security Requirements

- Never expose provider secrets in frontend.
- Keep `AUTH_BOOTSTRAP_KEY` unset in public production.
- Use HTTPS-only domains for app and API.
- Keep `ALLOWED_ORIGINS` explicit; do not use `*` with credentials.
