from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
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

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    setup_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="Salty Pickle Training Scheduler",
    version="0.1.0",
    lifespan=lifespan,
)

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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
