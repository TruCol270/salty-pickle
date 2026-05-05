# Custom Domains

Recommended production split:

- `app.example.com` -> Vercel frontend
- `api.example.com` -> Railway backend

## Vercel Frontend

1. Open the Vercel project.
2. Go to Settings -> Domains.
3. Add `app.example.com`.
4. Add the DNS record Vercel shows, usually:
   - `CNAME app cname.vercel-dns.com`
5. Set `VITE_API_BASE_URL=https://api.example.com` in Vercel environment
   variables.
6. Redeploy the frontend.

## Railway API

1. Open the Railway backend service.
2. Go to Settings -> Networking.
3. Add `api.example.com` as a custom domain.
4. Add the DNS record Railway shows, usually a `CNAME`.
5. Set backend environment variables:
   - `API_PUBLIC_URL=https://api.example.com`
   - `APP_PUBLIC_URL=https://app.example.com`
   - `FRONTEND_BASE_URL=https://app.example.com`
   - `FRONTEND_URL=https://app.example.com`
   - `ALLOWED_ORIGINS=https://app.example.com`
6. Redeploy the backend.

## DNS Validation

After DNS propagates:

```bash
curl -fsS https://api.example.com/live
curl -fsS https://api.example.com/healthz
```

Then open `https://app.example.com` and smoke test login, OAuth redirects, and
core API calls.
