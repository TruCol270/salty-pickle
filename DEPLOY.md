# Deployment

Salty Pickle deploys from GitHub using Railway for the FastAPI/PostgreSQL/Redis backend and Vercel for the React/Vite frontend.

## CI

GitHub Actions runs `.github/workflows/ci.yml` on every branch push and on pull requests targeting `main`.

- Backend job: installs Python dependencies, runs `ruff`, applies Alembic migrations against CI Postgres, and runs `pytest`.
- Frontend job: installs npm dependencies, runs TypeScript typecheck, and builds the Vite app.
- Docker job: builds the production Docker image after backend and frontend checks pass.

The backend CI job includes Postgres and Redis service containers so migration and cache-dependent checks use production-like dependencies.

## Railway Backend

1. Create a Railway project and connect it to the GitHub repository.
2. Configure the backend service to deploy from `main`.
3. Use the repository `Dockerfile` and `railway.toml`.
4. Provision Railway Postgres and Redis, then set `DATABASE_URL` and `REDIS_URL` from those services.
5. Set production secrets in Railway Variables, including `SECRET_KEY`, OAuth credentials, public callback URLs, `OPENAI_API_KEY`, and allowed frontend origins.
6. Keep the Railway deploy health check pointed at `/live`.

Railway GitHub integration should remain enabled so pushes to `main` automatically build and deploy the backend after branch protection allows the merge.

## Vercel Frontend

1. Import the GitHub repository into Vercel.
2. Set the project root to `frontend`.
3. Use the default Vite build command, `npm run build`, and output directory, `dist`.
4. Set frontend environment variables in Vercel, including `VITE_API_BASE_URL` pointing at the Railway API origin.
5. Configure production deployment from `main`.

Vercel GitHub integration should remain enabled so pushes to `main` automatically build and deploy the frontend after branch protection allows the merge.

## Branch Protection

Protect `main` in GitHub repository settings:

- Require pull requests before merging.
- Require the `backend`, `frontend`, and `docker` CI checks to pass.
- Require branches to be up to date before merging when practical.
- Restrict direct pushes to `main`.
- Keep Railway and Vercel deployments sourced from `main`, not feature branches.

Feature branches can still be pushed freely; CI will run on each branch push so pull requests arrive with current status checks.
