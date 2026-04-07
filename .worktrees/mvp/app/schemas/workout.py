from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class WorkoutBase(BaseModel):
    source: str
    start_time: datetime
    actual_distance_km: Optional[float] = None
    actual_duration_seconds: Optional[int] = None
    actual_pace_min_per_km: Optional[float] = None
    actual_elevation_m: Optional[float] = None
    average_heart_rate: Optional[float] = None
    max_heart_rate: Optional[float] = None
    notes: Optional[str] = None


class WorkoutCreate(WorkoutBase):
    source_id: Optional[str] = None
    raw_data: Optional[str] = None


class WorkoutResponse(WorkoutBase):
    id: int
    user_id: int
    planned_workout_id: Optional[int] = None
    performance_score: Optional[float] = None
    workout_type: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkoutSyncResponse(BaseModel):
    synced_count: int
    workouts: list[WorkoutResponse]
