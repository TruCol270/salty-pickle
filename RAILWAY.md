# Railway Deployment Configuration

This document describes the Railway-specific environment variables and configuration for deploying the Salty Pickle backend.

## Required Environment Variables

### Database & Cache
- **`DATABASE_URL`** - PostgreSQL connection string (auto-injected by Railway Postgres plugin)
  - Format: `postgresql://user:password@host:port/database`
  - Example: `postgresql://postgres:password@postgres.railway.internal:5432/railway`

- **`REDIS_URL`** - Redis connection string (auto-injected by Railway Redis plugin)  
  - Format: `redis://host:port/db`
  - Example: `redis://redis.railway.internal:6379/0`

### Server Configuration
- **`PORT`** - Server port (auto-injected by Railway, defaults to 8080)
- **`SECRET_KEY`** - JWT signing key (required for production)
  - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### CORS Configuration
- **`FRONTEND_URL`** - Frontend URL(s) for CORS (comma-separated list)
  - Example: `https://myapp.vercel.app`
  - Example (multiple): `https://myapp.vercel.app,https://staging.myapp.vercel.app`
  
- **`ALLOWED_ORIGINS`** - Legacy CORS origins (comma-separated, still supported)
  - Used in conjunction with FRONTEND_URL
  - Defaults to localhost URLs for development

### OAuth Integration
- **`STRAVA_CLIENT_ID`** - Strava OAuth client ID
- **`STRAVA_CLIENT_SECRET`** - Strava OAuth client secret
- **`STRAVA_REDIRECT_URI`** - Strava OAuth callback URL
  - Should be: `https://your-api-domain.railway.app/auth/strava/callback`

- **`GOOGLE_CLIENT_ID`** - Google OAuth client ID  
- **`GOOGLE_CLIENT_SECRET`** - Google OAuth client secret
- **`GOOGLE_REDIRECT_URI`** - Google OAuth callback URL
  - Should be: `https://your-api-domain.railway.app/auth/google/callback`

- **`WHOOP_CLIENT_ID`** - Whoop OAuth client ID
- **`WHOOP_CLIENT_SECRET`** - Whoop OAuth client secret  
- **`WHOOP_REDIRECT_URI`** - Whoop OAuth callback URL
  - Should be: `https://your-api-domain.railway.app/auth/whoop/callback`

### AI Integration
- **`OPENAI_API_KEY`** - OpenAI API key for GPT-4o

### Optional Configuration
- **`DEBUG`** - Enable debug mode (default: `false`)
- **`ENABLE_SCHEDULER`** - Enable background job scheduler (default: `false`)
- **`WORKER_SERVICE`** - Deploy as worker instead of web service (default: `false`)
- **`RAW_PAYLOAD_RETENTION_DAYS`** - Data retention period (default: `90`)
- **`AUTH_BOOTSTRAP_KEY`** - Bootstrap auth token for ops (optional)

## Railway Configuration

### Build Configuration (`railway.toml`)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
healthcheckPath = "/live"
releaseCommand = "alembic upgrade head"
```

### Health Endpoints
- **`/live`** - Basic liveness check (returns `{"status": "alive"}`)
- **`/healthz`** - Database connectivity check (returns 503 if DB unavailable)
- **`/health`** - Legacy health check (returns `{"status": "healthy"}`)

### Automatic Setup
Railway automatically provides:
1. **DATABASE_URL** via Postgres plugin
2. **REDIS_URL** via Redis plugin  
3. **PORT** environment variable
4. **Domain** with HTTPS certificate
5. **Deployments** on git push

### Migration Strategy
- Database migrations run automatically via `releaseCommand` in `railway.toml`
- Migrations execute before each deployment using `alembic upgrade head`
- Failed migrations prevent deployment

## Deployment Steps

1. **Connect Repository**
   ```bash
   railway login
   railway link [project-id]
   ```

2. **Add Database & Redis**
   ```bash
   railway add postgresql
   railway add redis
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set SECRET_KEY=your-secret-key
   railway variables set FRONTEND_URL=https://your-frontend.vercel.app
   railway variables set STRAVA_CLIENT_ID=your-strava-id
   # ... set other OAuth and API keys
   ```

4. **Deploy**
   ```bash
   git push origin main
   ```
   Or trigger manual deployment:
   ```bash
   railway up
   ```

## Troubleshooting

### Common Issues

**Build Failures:**
- Check Dockerfile syntax
- Ensure requirements.txt is present
- Frontend build errors (Node.js memory issues)

**Startup Failures:**  
- Missing required environment variables
- Database connection errors (check DATABASE_URL)
- Migration failures (check logs for SQL errors)

**CORS Errors:**
- Verify FRONTEND_URL matches your frontend domain
- Check browser console for specific origin errors
- Ensure HTTPS in production

### Logs
```bash
railway logs
railway logs --tail
```

### Database Access
```bash
railway connect postgresql
```

### Domain Configuration
- Railway provides automatic HTTPS domains
- Custom domains can be configured in Railway dashboard
- Update OAuth redirect URIs when using custom domains
