from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.services.analytics import AnalyticsService
from app.services.performance_analyzer import PerformanceAnalyzer

router = APIRouter()


@router.get("/performance")
async def get_performance_trends(
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        return {"error": "No user found"}

    service = AnalyticsService(db)
    return await service.get_performance_trends(user.id, days=days)


@router.get("/plan-progress/{plan_id}")
async def get_plan_progress(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_plan_progress(plan_id)


@router.post("/performance-check")
async def run_performance_check(
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger performance check to cross-reference Strava with planned workouts."""
    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.strava_access_token:
        raise HTTPException(status_code=400, detail="Please connect Strava first")

    analyzer = PerformanceAnalyzer(db)
    result = await analyzer.run_daily_performance_check(user)

    return result
