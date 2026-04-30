# OAuth provider dashboards (production)

Provider callbacks must hit the **API** host, not the Lovable/Vercel frontend.

## Callback URLs to register

Use the same host as `API_PUBLIC_URL` / `STRAVA_REDIRECT_URI` / `GOOGLE_REDIRECT_URI` / `WHOOP_REDIRECT_URI`.

| Provider | Callback path |
|----------|----------------|
| Strava | `{API_ORIGIN}/auth/strava/callback` |
| Google | `{API_ORIGIN}/auth/google/callback` |
| Whoop | `{API_ORIGIN}/auth/whoop/callback` |

Generate the three lines from your shell (see `scripts/print_oauth_callback_urls.sh`):

```bash
./scripts/print_oauth_callback_urls.sh https://api.yourdomain.com
```

## Where to configure

- **Strava:** [My API Application](https://www.strava.com/settings/api) — Authorization Callback Domain / Redirect URI must match `STRAVA_REDIRECT_URI` exactly.
- **Google Cloud Console:** APIs & Services → Credentials → your OAuth 2.0 Client → Authorized redirect URIs — must include `GOOGLE_REDIRECT_URI`.
- **Whoop Developer:** [developer.whoop.com](https://developer.whoop.com) — application redirect URI must match `WHOOP_REDIRECT_URI`.

## Frontend `redirect_url` flow

The app starts OAuth with `redirect_url` pointing at the **frontend** (e.g. `https://app.yourdomain.com/integrations`). That origin must appear in `ALLOWED_ORIGINS` (and match `validate_oauth_redirect_url_param`). After consent, the API redirects the browser back to that URL with `access_token` (and `user_id`) in the fragment.

## Checklist before go-live

- [ ] All three provider callbacks updated to production API domain
- [ ] `GET /auth/provider-callbacks` on the API returns expected URIs and allowed origins
- [ ] Test Strava connect from the real frontend origin (not only localhost)
- [ ] Google Calendar and Whoop use authenticated `POST /auth/*/authorize-url` after login
