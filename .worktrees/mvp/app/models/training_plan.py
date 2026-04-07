from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class PlanStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    goal_race_name = Column(String, nullable=True)
    goal_race_date = Column(DateTime, nullable=True)
    goal_distance_km = Column(Float, nullable=True)
    goal_time_seconds = Column(Integer, nullable=True)

    status = Column(String, default=PlanStatus.ACTIVE)
    current_week_number = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="training_plans")
    planned_workouts = relationship(
        "PlannedWorkout", back_populates="plan", cascade="all, delete-orphan"
    )


class PlannedWorkout(Base):
    __tablename__ = "planned_workouts"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(
        Integer, ForeignKey("training_plans.id"), nullable=False, index=True
    )

    week_number = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)

    workout_type = Column(String, nullable=False)

    target_distance_km = Column(Float, nullable=True)
    target_duration_minutes = Column(Integer, nullable=True)
    target_pace_min_per_km = Column(Float, nullable=True)
    target_elevation_m = Column(Float, nullable=True)

    flexible = Column(String, default="true")
    notes = Column(Text, nullable=True)

    scheduled_date = Column(DateTime, nullable=True)
    calendar_event_id = Column(String, nullable=True)
    completed = Column(String, default="false")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("TrainingPlan", back_populates="planned_workouts")
    completed_workout = relationship(
        "CompletedWorkout", back_populates="planned_workout", uselist=False
    )
