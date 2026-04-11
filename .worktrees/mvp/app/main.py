import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.exceptions import (
    IntegrationError,
    ResourceNotFoundError,
    SaltyPickleError,
    ValidationError,
)
from app.api import (
    auth,
    workouts,
    plans,
    calendar,
    analytics,
    preferences,
    races,
    whoop,
)
from app.scheduler.jobs import setup_scheduler, shutdown_scheduler

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    setup_scheduler()
    yield
    shutdown_scheduler()


limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="Salty Pickle Training Scheduler",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(workouts.router, prefix="/api/v1/workouts", tags=["workouts"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["plans"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(preferences.router, prefix="/api/v1/user", tags=["user"])
app.include_router(races.router, prefix="/api/v1/races", tags=["races"])
app.include_router(whoop.router, prefix="/api/v1/whoop", tags=["whoop"])

_ERROR_CODE_MAP = {
    ResourceNotFoundError: ("not_found", 404),
    IntegrationError: ("integration_error", 502),
    ValidationError: ("validation_error", 422),
    SaltyPickleError: ("server_error", 500),
}


@app.exception_handler(SaltyPickleError)
async def salty_pickle_error_handler(request: Request, exc: SaltyPickleError):
    code, status = _ERROR_CODE_MAP.get(type(exc), ("server_error", 500))
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc), "details": None}},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    message = first.get("msg", "Validation error")
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": message, "details": errors}},
    )


@app.get("/live")
async def liveness():
    return {"status": "alive"}


@app.get("/healthz")
async def readiness():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "db": "ok"}
    except Exception:
        logger.exception("Healthz DB check failed")
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    return HTMLResponse(content=PRIVACY_POLICY_HTML)


@app.get("/redirect", response_class=HTMLResponse)
async def oauth_redirect():
    return HTMLResponse(content=REDIRECT_HTML)


PRIVACY_POLICY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Privacy Policy – Salty Pickle</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 24px; color: #1a1a1a; line-height: 1.7; }
    h1 { font-size: 2rem; font-weight: 700; margin-bottom: 8px; }
    h2 { font-size: 1.25rem; font-weight: 600; margin-top: 36px; }
    p, li { color: #444; }
    ul { padding-left: 24px; }
    .updated { color: #888; font-size: 0.9rem; margin-bottom: 32px; }
    a { color: #4f46e5; }
  </style>
</head>
<body>
  <h1>Privacy Policy</h1>
  <p class="updated">Last updated: April 2026</p>

  <p>Salty Pickle ("we", "us", or "our") is a personal training plan scheduler that connects
  to Strava, Google Calendar, and Whoop to help you train smarter. This policy explains what
  data we collect and how we use it.</p>

  <h2>1. Data We Collect</h2>
  <ul>
    <li><strong>Strava:</strong> Athlete ID, completed activity data (distance, duration, heart rate, pace)</li>
    <li><strong>Google:</strong> Email address, Google Calendar access to create and manage training events</li>
    <li><strong>Whoop:</strong> Recovery scores, sleep performance, resting heart rate, HRV</li>
    <li><strong>You provide:</strong> Race goals, fitness level, training preferences, injury history</li>
  </ul>

  <h2>2. How We Use Your Data</h2>
  <ul>
    <li>Generate personalized training plans based on your fitness history and goals</li>
    <li>Sync training workouts to your Google Calendar</li>
    <li>Cross-reference completed workouts with your plan to track progress</li>
    <li>Adjust your plan based on Whoop recovery scores</li>
    <li>Improve future plan recommendations</li>
  </ul>

  <h2>3. Data Storage</h2>
  <p>Your data is stored in a private PostgreSQL database. OAuth tokens are stored securely
  and used only to access the services you have connected. We do not sell or share your
  data with third parties.</p>

  <h2>4. Third-Party Services</h2>
  <p>We integrate with:</p>
  <ul>
    <li><a href="https://www.strava.com/legal/privacy">Strava Privacy Policy</a></li>
    <li><a href="https://policies.google.com/privacy">Google Privacy Policy</a></li>
    <li><a href="https://www.whoop.com/privacy/">Whoop Privacy Policy</a></li>
  </ul>

  <h2>5. Revoking Access</h2>
  <p>You can disconnect any integration at any time:</p>
  <ul>
    <li><strong>Strava:</strong> <a href="https://www.strava.com/settings/apps">strava.com/settings/apps</a></li>
    <li><strong>Google:</strong> <a href="https://myaccount.google.com/permissions">myaccount.google.com/permissions</a></li>
    <li><strong>Whoop:</strong> via Whoop app settings</li>
  </ul>

  <h2>6. Contact</h2>
  <p>Questions? Open an issue on <a href="https://github.com/TruCol270/salty-pickle">GitHub</a>.</p>
</body>
</html>"""


REDIRECT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Connected – Salty Pickle</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f0f4ff; }
    .card { background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 48px; text-align: center; max-width: 420px; width: 100%; }
    .icon { font-size: 3rem; margin-bottom: 16px; }
    h1 { font-size: 1.5rem; font-weight: 700; color: #1a1a1a; margin: 0 0 8px; }
    p { color: #666; margin: 0 0 24px; }
    a { display: inline-block; background: #4f46e5; color: white; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; }
    a:hover { background: #4338ca; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✅</div>
    <h1>Connected!</h1>
    <p>Your account has been successfully connected to Salty Pickle.</p>
    <a href="http://localhost:3000">Go to Dashboard</a>
  </div>
</body>
</html>"""
