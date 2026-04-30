# Salty Pickle — Overhaul & 90's Grunge Redesign Plan

_Approved via ultraplan browser session. Save this file to resume work if session ends._

---

## Status Tracker

- [x] **Phase 1A** — Bug fixes (backend: NameError, dead code, misplaced imports)
- [x] **Phase 1B** — Backend foundation (exceptions.py, global handler, /healthz, /live, scheduler logging, HTTP 404/ValueError handlers, structlog)
- [x] **Phase 1C** — DevOps fixes (docker-compose CMD, health checks, Makefile)
- [x] **Phase 1D** — Frontend foundation (api.ts, types/index.ts, LoadingSpinner, ErrorBoundary)
- [x] **Phase 1E** — Frontend page fixes (loading/error states, Whoop trend API + no mock data, shared `api` client)
- [x] **Phase 2** — Design system (grunge tokens in Tailwind/CSS, Button/Card/Input/Navigation, sidebar layout)
- [x] **Phase 3** — Page redesigns (sidebar “Mission Control” shell + tokens; full per-page grunge content polish optional with Figma)
- [x] **Phase 4** — Backend optimization (Redis cache on analytics, SlowAPI on performance-check, structlog, OAuth state 15m TTL; boolean columns documented for future migration)
- [x] **Phase 5** — DevOps improvements (multi-stage Dockerfile, `nginx.example.conf` with `X-Real-IP` and timeouts)
- [x] **Phase 6** — Polish & launch (axios bumped, `npm audit` clean for prod deps; Lighthouse and formal UAT remain manual)

---

## Context

Comprehensive review of the MVP codebase revealed several bugs and missing patterns, plus a user-approved redesign to a 90's grunge/hip-hop aesthetic (Tony Hawk Pro Skater). The ultraplan was approved via browser session. A Figma sub-agent is running in the background to generate design mockups for Phase 2+3 approval.

---

## Confirmed Bugs to Fix Immediately

1. **`analytics.py` NameError** — `HTTPException` is used at line ~60 but never imported → `/api/v1/analytics/performance-check` crashes with `NameError`
2. **`calendar_sync.py` dead code** — `update_calendar_event` has unreachable code block after `return` (lines 148-173)
3. **`races.py` misplaced import** — `from datetime import datetime` is at line 47 *after* the route definition (bottom of file)
4. **`docker-compose.yml` CMD override** — `api` service overrides the Dockerfile's clean uvicorn CMD with a Python one-liner; revert to Dockerfile CMD
5. **`Makefile` db-reset bug** — second `alembic upgrade head` runs on host instead of inside Docker

---

## Phase 1: Foundation & Fixes

### 1A — Backend Bug Fixes

**`app/api/analytics.py`**
- Add `from fastapi import HTTPException` to imports

**`app/services/calendar_sync.py`**
- Remove dead code block after `return` in `update_calendar_event` (lines 148-173)

**`app/api/races.py`**
- Move `from datetime import datetime` from line 47 to top-of-file with other imports

### 1B — Backend Foundation

**Create `app/exceptions.py`:**
```python
class SaltyPickleError(Exception): ...
class ResourceNotFoundError(SaltyPickleError): ...
class IntegrationError(SaltyPickleError): ...
class ValidationError(SaltyPickleError): ...
```

**Modify `app/main.py`:**
- Register `@app.exception_handler` for `SaltyPickleError`, `ValueError`, `RequestValidationError`
- Standard error response format: `{"error": {"code": str, "message": str, "details": any}}`
- Add `GET /healthz` — checks DB connectivity (`SELECT 1`), returns `{"status":"ready","db":"ok"}` or 503
- Add `GET /live` — no DB check, returns `{"status":"alive"}`
- Replace all `print()` in scheduler jobs with `logging.getLogger(__name__)`

### 1C — DevOps Fixes

**`docker-compose.yml`:**
- Remove CMD override on `api` service (use Dockerfile's uvicorn CMD)
- Add health check to `api`: `curl -f http://localhost:8000/live || exit 1`
- Add health check to `db`: `pg_isready -U postgres`

**`Makefile`:**
- Fix `db-reset`: prefix second alembic command with `docker-compose run api`

### 1D — Frontend Foundation

**Create `frontend/src/lib/api.ts`:**
```typescript
const api = axios.create({ baseURL: '/' });
// Response interceptor: normalize errors to { message, code }
export default api;
```

**Create `frontend/src/types/index.ts`:**
- `Workout`, `WorkoutStats`, `TrainingPlan`, `PlannedWorkout`, `UserPreferences`, `IntegrationStatus`
- Eliminates duplicated inline type definitions across pages

**Create `frontend/src/components/LoadingSpinner.tsx`:**
- Props: `size?: 'sm' | 'md' | 'lg'`, `className?`
- Uses `animate-spin rounded-full border-b-2` pattern

**Create `frontend/src/components/ErrorBoundary.tsx`:**
- Catches render errors, shows message + retry button
- Applied at Route level in App.tsx

**Modify `frontend/src/App.tsx`:**
- Wrap routes with `<ErrorBoundary>`
- Set `QueryClient` `defaultOptions`: `{ queries: { staleTime: 30_000, retry: 1 } }`

### 1E — Frontend Page Fixes

**`frontend/src/pages/Dashboard.tsx`:**
- Replace bare `"Loading..."` text with `<LoadingSpinner />`
- Add `isError` branch with error message display
- Refactor all axios calls to use `api` from `src/lib/api.ts`

**`frontend/src/pages/PlanEditor.tsx`:**
- Replace bare `"Loading..."` with `<LoadingSpinner />`
- Refactor axios to use `api`
- Add onClick handler to "Sync to Calendar" button (`POST /api/v1/calendar/sync`)

**`frontend/src/pages/StravaPage.tsx`:**
- Add `isError` error state
- Refactor axios to use `api`

**`frontend/src/pages/WhoopPage.tsx`:**
- Remove hardcoded mock 7-day trend data array
- Use real data from API or show empty state
- Refactor axios to use `api`

**`frontend/src/pages/CreatePlan.tsx`:**
- Refactor axios to use `api`

**`frontend/src/pages/PreferencesPage.tsx`:**
- Refactor axios to use `api`

---

## Phase 2: Design System (PENDING Figma approval)

Do not implement until Figma mockups reviewed and approved.

**Design tokens (90's grunge/hip-hop, Tony Hawk Pro Skater):**
- `grunge.acid: '#CCFF00'` — primary accent/energy
- `grunge.pink: '#FF00FF'` — secondary accent/urgency
- `grunge.black: '#0A0E27'` — backgrounds
- `grunge.charcoal: '#1F1F2E'` — elevated surfaces/cards
- `grunge.blue: '#00FFFF'` — hover/links
- `grunge.orange: '#FF6600'` — warnings
- `grunge.purple: '#9D00FF'` — success/completion

**`frontend/tailwind.config.js`** — extend theme with above palette, custom shadows (neon glow), glitch keyframes

**`frontend/src/index.css`** — film grain texture overlay, CSS custom properties

**New components:** `Button.tsx`, `Card.tsx`, `Input.tsx`, `Navigation.tsx` (sidebar replaces header nav)

**Replace `Layout.tsx`** — horizontal nav → sidebar navigation

---

## Phase 3: Page Redesigns (PENDING Phase 2 approval)

Pages to redesign in order:
1. Dashboard → "Mission Control" — hero banner with grunge texture, neon-bordered stat cards, gradient progress bars
2. CreatePlan → "Build Your Plan" — punk stepper, grunge inputs, live preview card
3. PlanEditor → "Shred Your Workout" — timeline with neon accents, glitch hover on action buttons
4. PreferencesPage → "Settings" — grouped grunge form sections, integration status display
5. IntegrationsPage → "Connections" — large connect buttons with neon effects, status indicators

---

## Phase 4: Backend Optimization

- Redis caching on `GET /api/v1/plans/active`, analytics endpoints (70%+ target cache hit rate)
- Rate limiting via SlowAPI middleware
- Structured logging via structlog (JSON output)
- OAuth state expiry enforcement (15-min TTL strict validation on use)
- Fix Boolean fields stored as String (`completed`, `flexible`, `applied`)

---

## Phase 5: DevOps Improvements

- Backend Dockerfile: multi-stage build (builder → slim runtime)
- Cloud Build: verify image sizes, add canary deployment step
- Add `proxy_set_header X-Real-IP` and `proxy_read_timeout` to nginx.conf

---

## Phase 6: Polish & Launch

- Lighthouse score ≥ 80 mobile, ≥ 90 desktop
- npm audit + bandit security scan clean
- User acceptance testing sign-off

---

## Critical File Map

| File | Phase | Action |
|------|-------|--------|
| `app/api/analytics.py` | 1A | Add missing `HTTPException` import |
| `app/services/calendar_sync.py` | 1A | Remove dead code (lines 148-173) |
| `app/api/races.py` | 1A | Move `datetime` import to top |
| `app/exceptions.py` | 1B | CREATE — exception hierarchy |
| `app/main.py` | 1B | Global exception handlers, /healthz, /live, logging |
| `docker-compose.yml` | 1C | Fix CMD override, add health checks |
| `Makefile` | 1C | Fix db-reset bug |
| `frontend/src/lib/api.ts` | 1D | CREATE — shared axios instance |
| `frontend/src/types/index.ts` | 1D | CREATE — shared types |
| `frontend/src/components/LoadingSpinner.tsx` | 1D | CREATE |
| `frontend/src/components/ErrorBoundary.tsx` | 1D | CREATE |
| `frontend/src/App.tsx` | 1D | QueryClient config, ErrorBoundary |
| `frontend/src/pages/Dashboard.tsx` | 1E | Loading/error states, api client |
| `frontend/src/pages/PlanEditor.tsx` | 1E | Loading state, sync handler, api client |
| `frontend/src/pages/StravaPage.tsx` | 1E | Error state, api client |
| `frontend/src/pages/WhoopPage.tsx` | 1E | Remove mock data, api client |
| `frontend/src/pages/CreatePlan.tsx` | 1E | api client refactor |
| `frontend/src/pages/PreferencesPage.tsx` | 1E | api client refactor |
| `frontend/tailwind.config.js` | 2 | Grunge theme extension |
| `frontend/src/index.css` | 2 | Film grain, CSS vars |

---

## Verification

### Phase 1 Backend
- `docker-compose up` — api starts without Python one-liner CMD
- `curl http://localhost:8000/live` → `{"status":"alive"}` (200)
- `curl http://localhost:8000/healthz` → `{"status":"ready","db":"ok"}` (200)
- `curl -X POST http://localhost:8000/api/v1/analytics/performance-check` → no NameError
- Deliberate 404 → `{"error":{"code":"not_found","message":"..."}}` format

### Phase 1 Frontend
- Dashboard shows `<LoadingSpinner />` while loading (not bare "Loading...")
- Dashboard shows error UI when API unreachable
- WhoopPage shows empty/real state (no hardcoded 7-day mock array)
- PlanEditor "Sync to Calendar" fires POST and shows success/error feedback
- All pages import from `src/lib/api.ts` (no raw `axios.get` directly in components)

### Phase 2+ (after Figma approval)
- All grunge color tokens appear in browser devtools
- Glitch animation triggers on button hover
- Film grain texture visible on page backgrounds
- Mobile layout functional at 375px viewport
