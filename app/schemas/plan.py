from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class PlannedWorkoutBase(BaseModel):
    week_number: int
    day_of_week: int
    workout_type: str
    target_distance_km: Optional[float] = None
    target_duration_minutes: Optional[int] = None
    target_pace_min_per_km: Optional[float] = None
    target_elevation_m: Optional[float] = None
    flexible: bool = True
    notes: Optional[str] = None


class PlannedWorkoutCreate(PlannedWorkoutBase):
    pass


class PlannedWorkoutResponse(PlannedWorkoutBase):
    id: int
    plan_id: int
    scheduled_date: Optional[datetime] = None
    calendar_event_id: Optional[str] = None
    completed: bool = False

    model_config = {"from_attributes": True}


class TrainingPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    goal_race_name: Optional[str] = None
    goal_race_date: Optional[datetime] = None
    goal_distance_km: Optional[float] = None


class TrainingPlanCreate(TrainingPlanBase):
    workouts: list[PlannedWorkoutCreate]


class TrainingPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    current_week_number: Optional[int] = None


class TrainingPlanResponse(TrainingPlanBase):
    id: int
    user_id: int
    status: str
    current_week_number: int
    workouts: list[PlannedWorkoutResponse] = Field(
        default_factory=list,
        validation_alias="planned_workouts",
    )
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanAdjustmentRequest(BaseModel):
    workout_id: Optional[int] = None
    trigger: str
    reason: Optional[str] = None


class PlanAdjustmentResponse(BaseModel):
    adjustment_id: int
    adjustment_type: str
    new_workouts: list[PlannedWorkoutResponse]
    message: str


class AIGenerateRequest(BaseModel):
    race_name: str
    race_date: datetime
    race_distance_km: float
    current_fitness_level: str = "intermediate"
    weekly_mileage_km: float = 30
    years_experience: str = "3-5"
    preferred_days: Optional[list[int]] = None
    preferred_time: str = "morning"


class AIGenerateResponse(BaseModel):
    plan_id: int
    weeks: int
    strava_analysis: dict
