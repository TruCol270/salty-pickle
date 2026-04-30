from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.calendar import CalendarSyncResponse, CalendarEventResponse
from app.services.calendar_sync import CalendarSyncService

router = APIRouter()


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_plan_to_calendar(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.google_access_token:
        raise HTTPException(status_code=400, detail="Google Calendar not connected")

    service = CalendarSyncService(db)
    events = await service.sync_plan_to_calendar(user, plan_id)

    return CalendarSyncResponse(
        synced_count=len(events),
        events=events,
    )


@router.get("/events")
async def get_calendar_events(
    days: int = Query(default=14, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.google_access_token:
        raise HTTPException(status_code=400, detail="Google Calendar not connected")

    from app.services.google_calendar import GoogleCalendarService

    calendar_service = GoogleCalendarService(db)

    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    events = await calendar_service.get_events(user, now, end_date)

    return {"events": events}
