from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.limiter import limiter
from app.cache import cache_get_json, cache_set_json
from app.models import User
from app.services.analytics import AnalyticsService
from app.services.performance_analyzer import PerformanceAnalyzer

router = APIRouter()


@router.get("/performance")
async def get_performance_trends(
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cache_key = f"analytics:perf:{user.id}:{days}"
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return cached

    service = AnalyticsService(db)
    data = await service.get_performance_trends(user.id, days=days)
    await cache_set_json(cache_key, data, ttl_seconds=120)
    return data


@router.get("/plan-progress/{plan_id}")
async def get_plan_progress(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cache_key = f"analytics:plan_progress:{plan_id}:{user.id}"
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return cached

    service = AnalyticsService(db)
    data = await service.get_plan_progress(plan_id)
    await cache_set_json(cache_key, data, ttl_seconds=90)
    return data


@router.post("/performance-check")
@limiter.limit("30/minute")
async def run_performance_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Manually trigger performance check to cross-reference Strava with planned workouts."""
    if not user.strava_access_token:
        raise HTTPException(status_code=400, detail="Please connect Strava first")

    analyzer = PerformanceAnalyzer(db)
    result = await analyzer.run_daily_performance_check(user)

    return result
