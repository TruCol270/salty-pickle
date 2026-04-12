from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models import User

router = APIRouter()


@router.get("")
async def get_integration_status(
    user: User = Depends(get_current_user),
):
    return {
        "strava": {
            "connected": bool(user.strava_access_token),
            "athlete_id": user.strava_athlete_id,
        },
        "google": {
            "connected": bool(user.google_access_token),
            "calendar_id": user.google_calendar_id,
        },
        "whoop": {
            "connected": bool(user.whoop_access_token),
            "user_id": user.whoop_user_id,
        },
    }


