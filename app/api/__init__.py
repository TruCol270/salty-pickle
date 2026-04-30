from app.api.auth import router as auth_router
from app.api.workouts import router as workouts_router
from app.api.plans import router as plans_router
from app.api.calendar import router as calendar_router
from app.api.analytics import router as analytics_router
from app.api.integrations import router as integrations_router

__all__ = [
    "auth_router",
    "workouts_router",
    "plans_router",
    "calendar_router",
    "analytics_router",
    "integrations_router",
]
