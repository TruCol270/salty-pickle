from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    timezone: str = "America/New_York"
    units: str = "km"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    timezone: Optional[str] = None
    units: Optional[str] = None
    min_recovery_threshold: Optional[float] = None
    low_hrv_threshold_ms: Optional[float] = None


class UserResponse(UserBase):
    id: int
    strava_connected: bool = False
    google_connected: bool = False
    whoop_connected: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPreferencesUpdate(BaseModel):
    preferred_workout_days: Optional[str] = None
    preferred_workout_time: Optional[str] = None
    available_equipment: Optional[str] = None
    injury_history: Optional[str] = None
    sleep_hours_target: Optional[float] = None


class UserPreferencesResponse(BaseModel):
    preferred_workout_days: Optional[str] = None
    preferred_workout_time: str = "morning"
    available_equipment: Optional[str] = None
    injury_history: Optional[str] = None
    sleep_hours_target: Optional[float] = None
