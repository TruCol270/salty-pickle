# Vercel Deployment Configuration

## Framework Detection

- **Framework:** React + Vite + TypeScript
- **Auto-Detection:** Vercel automatically detects Vite projects
- **Build Command:** `npm run build` (maps to `vite build`)
- **Output Directory:** `dist/` (Vite default)
- **Install Command:** `npm ci`

## Build Configuration

The project uses Vite's default build configuration:

- Build script: `vite build`
- Output: static files to `dist/`
- Asset optimization: automatic via Vite
- TypeScript compilation: handled by Vite

## Environment Variables

Set `VITE_API_BASE_URL` in each Vercel environment.

```text
Production:  VITE_API_BASE_URL=https://api.yourdomain.com
Preview:     VITE_API_BASE_URL=https://api-staging.yourdomain.com
Development: VITE_API_BASE_URL=http://localhost:8080
```

`VITE_PUBLIC_API_URL` is supported as a compatibility alias, but
`VITE_API_BASE_URL` is preferred.

## API Configuration

- Centralized API client: `src/lib/api.ts`
- Environment helper: `src/lib/env.ts`
- All browser API calls should use the shared Axios client.
- Do not hardcode `localhost` or `127.0.0.1` in frontend source.

## Vercel Configuration

The project includes `vercel.json` for SPA routing and static asset caching.
Vercel preview deployments are automatic for pull requests when the GitHub
integration is enabled.

## Deployment Checklist

- Set `VITE_API_BASE_URL` for Production, Preview, and Development scopes.
- Confirm the Railway/API host is publicly reachable.
- Add the Vercel app domains to backend CORS via `FRONTEND_URL` or
  `ALLOWED_ORIGINS`.
- Run `npm run build` locally before first deploy.
- Smoke test login, OAuth redirects, and authenticated API calls after deploy.

## Troubleshooting

- Build cannot read env var: ensure the variable name starts with `VITE_`.
- Browser requests hit the wrong host: check `VITE_API_BASE_URL` in the target
  Vercel environment and redeploy.
- Refreshing a client route 404s: verify `vercel.json` rewrites all paths to
  `/index.html`.
- API requests fail CORS: add the exact Vercel origin to backend CORS.
