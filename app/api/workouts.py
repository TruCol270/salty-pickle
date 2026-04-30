from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.deps import get_current_user
from app.limiter import limiter
from app.models import User, CompletedWorkout
from app.schemas.workout import WorkoutResponse, WorkoutSyncResponse
from app.services.workout_sync import WorkoutSyncService

router = APIRouter()


@router.get("", response_model=list[WorkoutResponse])
async def list_workouts(
    limit: int = Query(default=30, le=100),
    offset: int = Query(default=0, ge=0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(CompletedWorkout).where(
        CompletedWorkout.user_id == user.id
    ).order_by(desc(CompletedWorkout.start_time))

    if start_date:
        query = query.where(CompletedWorkout.start_time >= start_date)
    if end_date:
        query = query.where(CompletedWorkout.start_time <= end_date)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/sync", response_model=WorkoutSyncResponse)
@limiter.limit("10/minute")
async def sync_workouts(
    request: Request,
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.strava_access_token:
        raise HTTPException(status_code=400, detail="Strava not connected")

    after = datetime.utcnow() - timedelta(days=days)

    service = WorkoutSyncService(db)
    synced = await service.sync_from_strava(user, after=after)

    return WorkoutSyncResponse(
        synced_count=len(synced),
        workouts=synced,
    )


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CompletedWorkout).where(
            CompletedWorkout.id == workout_id,
            CompletedWorkout.user_id == user.id,
        )
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    return workout
