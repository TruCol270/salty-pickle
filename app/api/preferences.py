from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.user import UserPreferencesUpdate, UserPreferencesResponse

router = APIRouter()


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    user: User = Depends(get_current_user),
):
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
    user: User = Depends(get_current_user),
):

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
