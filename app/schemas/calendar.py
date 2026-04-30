from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None


class CalendarEventResponse(BaseModel):
    id: str
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None


class CalendarSyncResponse(BaseModel):
    synced_count: int
    events: list[CalendarEventResponse]
