# Deployment Baseline - Salty Pickle

**Generated:** 2026-04-30  
**Audit Target:** salty-pickle repository

## 1. Repository Structure & Tech Stack

### Backend Service Location
- **Path:** `app/` directory
- **Language:** Python 3.11
- **Framework:** FastAPI
- **Package Manager:** pip (requirements.txt)
- **Entry Point:** `app/main.py`
- **Worker Entry:** `worker_main.py`

### Frontend App Location
- **Path:** `frontend/` directory
- **Language:** TypeScript
- **Framework:** React + Vite
- **Package Manager:** npm (package.json + package-lock.json)
- **Build Tool:** Vite

### Key Frameworks & Libraries
- **Backend:** FastAPI, SQLAlchemy (async), Alembic, APScheduler, Redis, HTTPX
- **Frontend:** React 18, TypeScript, TailwindCSS, React Query, Axios
- **Database ORM:** SQLAlchemy 2.0 (async)
- **Authentication:** JWT with python-jose
- **LLM:** OpenAI GPT-4o
- **Integrations:** Strava API, Google Calendar API, Whoop API

## 2. Environment Variables Inventory

### Backend Environment Variables (.env.example)
```
DATABASE_URL=postgresql://user:password@localhost:5432/salty_pickle
REDIS_URL=redis://localhost:6379/0
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
STRAVA_REDIRECT_URI=http://localhost:8080/auth/strava/callback
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your-secret-key-for-jwt
DEBUG=true
APP_PUBLIC_URL=http://localhost:5173
API_PUBLIC_URL=http://localhost:8080
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
FRONTEND_BASE_URL=http://localhost:5173
GCP_PROJECT_ID=your-gcp-project
GCP_REGION=us-central1
WHOOP_CLIENT_ID=your_whoop_client_id
WHOOP_CLIENT_SECRET=your_whoop_client_secret
WHOOP_REDIRECT_URI=http://localhost:8080/auth/whoop/callback
RAW_PAYLOAD_RETENTION_DAYS=90
ENABLE_SCHEDULER=false
WORKER_SERVICE=false
AUTH_BOOTSTRAP_KEY=(optional)
```

### Frontend Environment Variables (Build-time)
```
VITE_API_BASE_URL=(configured during Docker build)
```

## 3. Database Configuration

### Database Type
- **Primary:** PostgreSQL 15+ 
- **Cache:** Redis 7
- **ORM:** SQLAlchemy 2.0 with AsyncPG driver
- **Connection:** Configured via `DATABASE_URL` environment variable
- **Pool:** Async connection pool via `create_async_engine`

### Migration System
- **Tool:** Alembic
- **Config:** `alembic.ini`
- **Migrations Path:** Default Alembic structure
- **Auto-run:** Migrations execute on container startup via `alembic upgrade head`

### Connection Configuration
- File: `app/database.py`
- Async engine with AsyncPG driver
- Automatic postgres:// → postgresql+asyncpg:// URL conversion
- Connection verification on startup via `init_db()`

## 4. Deployment Files Inventory

### Present Files
- **Dockerfile** ✅ - Multi-stage build (Python deps + Frontend build + Runtime)
- **docker-compose.yml** ✅ - Full stack with PostgreSQL, Redis, API, Frontend
- **railway.toml** ✅ - Railway deployment config with release command
- **render.yaml** ✅ - Render.com deployment config
- **cloudbuild.yaml** ✅ - Google Cloud Build configuration
- **.dockerignore** ✅ - Docker build exclusions
- **nginx.example.conf** ✅ - Example reverse proxy config

### Missing Files
- **vercel.json** ❌ - No Vercel configuration
- **nixpacks.toml** ❌ - No Nixpacks configuration
- **Procfile** ❌ - No Heroku Procfile

## 5. Authentication & Security Configuration

### Authentication Mechanism
- **Type:** JWT (JSON Web Tokens)
- **Algorithm:** HS256
- **Provider:** python-jose library
- **Token Expiry:** 7 days (10080 minutes)
- **Implementation:** `app/security.py`

### Session Storage
- **Method:** Stateless JWT tokens (no server-side sessions)
- **OAuth State:** Stored in database (`oauth_state` model)
- **User Auth:** Bearer token in Authorization header

### CORS Configuration
- **Implementation:** FastAPI CORSMiddleware
- **Origins:** Configurable via `ALLOWED_ORIGINS` environment variable
- **Default Local:** localhost:5173, localhost:3000, 127.0.0.1 variants
- **Production:** Must be set to public origins only

### OAuth Integrations
- **Strava OAuth** - For workout data
- **Google OAuth** - For calendar sync
- **Whoop OAuth** - For recovery data
- **Redirect URIs:** Configurable via environment variables

## 6. Committed Secrets Scan

### Scan Results: NONE FOUND ✅

**Files Checked:**
- No `.env` files committed (only `.env.example` templates)
- Python source code: No hardcoded API keys or secrets
- TypeScript/JavaScript source: No hardcoded credentials
- Configuration files: All use environment variable references

**Secret Management Pattern:**
- All secrets referenced via environment variables
- Default values like "change-me-in-production" trigger runtime errors in production
- OAuth credentials properly externalized
- Database credentials use environment variable interpolation

## 7. Application Entry Points

### Backend Start Commands
- **Development:** `uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload`
- **Production:** `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`
- **Worker Service:** `python worker_main.py` (for scheduled jobs)
- **Docker CMD:** Runs migrations then starts uvicorn on container startup

### Frontend Commands
- **Development:** `npm run dev` (Vite dev server)
- **Build:** `npm run build` (Vite build to dist/)
- **Preview:** `npm run preview` (Serve built files)
- **Docker:** Built into static files served by FastAPI

### Database Commands
- **Migrations:** `alembic upgrade head`
- **New Migration:** `alembic revision --autogenerate -m "description"`

## 8. Test Setup & CI Configuration

### Test Framework
- **Backend:** pytest with pytest-asyncio and pytest-cov
- **Coverage Target:** Configured for coverage reporting
- **Test Database:** Separate test database in CI

### CI/CD Configuration
- **File:** `.github/workflows/ci.yml`
- **Triggers:** Push to main/mvp branches, PRs to main
- **Services:** PostgreSQL 15, Redis 7
- **Backend Jobs:**
  - Lint with ruff
  - Run Alembic migrations
  - Execute pytest suite
- **Frontend Jobs:**
  - npm ci install
  - npm run build
  - npm audit (security check)
- **Docker Job:**
  - Build complete Docker image
  - Runs after backend/frontend tests pass

### Test Environment
- **Database:** postgresql://test:test@localhost:5432/salty_pickle_test
- **Redis:** redis://localhost:6379/0
- **Secret Key:** ci-test-key-not-for-production
- **Debug:** Enabled in CI

---

## Summary for Railway + Vercel Deployment

### Backend Stack
- FastAPI (Python 3.11) with PostgreSQL + Redis
- Docker-ready with multi-stage build
- Railway deployment configured via railway.toml

### Frontend Stack  
- React + TypeScript + Vite
- Builds to static files, served by FastAPI in Docker
- Can be extracted for separate Vercel deployment

### Database Choice
- PostgreSQL with SQLAlchemy async ORM
- Alembic migrations auto-run on startup
- Redis for caching

### Secret Leak Count
- **0 secrets found** - All properly externalized to environment variables

### Deployment Blockers
- **None** - Repository is deployment-ready for Railway
- **For Vercel:** Frontend can be separated from Docker build
- **Required:** Environment variables must be configured in deployment platform
- **Database:** Requires PostgreSQL instance (Railway Postgres recommended)
- **Cache:** Requires Redis instance (Railway Redis recommended)

### Next Steps for Deployment
1. Configure environment variables in Railway
2. Connect PostgreSQL and Redis add-ons
3. Deploy backend to Railway
4. Frontend can deploy as-is (served by FastAPI) or separately to Vercel
