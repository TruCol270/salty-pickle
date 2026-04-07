from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.services.race_analyzer import RaceAnalyzer
from app.schemas.user import UserPreferencesUpdate, UserPreferencesResponse

router = APIRouter()


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserPreferencesResponse(
        preferred_workout_days=user.preferred_workout_days,
        preferred_workout_time=user.preferred_workout_time,
        available_equipment=user.available_equipment,
        injury_history=user.injury_history,
        sleep_hours_target=user.sleep_hours_target,
    )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    preferences: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if preferences.preferred_workout_days is not None:
        user.preferred_workout_days = preferences.preferred_workout_days
    if preferences.preferred_workout_time is not None:
        user.preferred_workout_time = preferences.preferred_workout_time
    if preferences.available_equipment is not None:
        user.available_equipment = preferences.available_equipment
    if preferences.injury_history is not None:
        user.injury_history = preferences.injury_history
    if preferences.sleep_hours_target is not None:
        user.sleep_hours_target = preferences.sleep_hours_target

    await db.commit()
    await db.refresh(user)

    return UserPreferencesResponse(
        preferred_workout_days=user.preferred_workout_days,
        preferred_workout_time=user.preferred_workout_time,
        available_equipment=user.available_equipment,
        injury_history=user.injury_history,
        sleep_hours_target=user.sleep_hours_target,
    )
