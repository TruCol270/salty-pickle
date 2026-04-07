from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)

    strava_athlete_id = Column(String, unique=True, nullable=True, index=True)
    google_calendar_id = Column(String, nullable=True)

    strava_access_token = Column(String, nullable=True)
    strava_refresh_token = Column(String, nullable=True)
    strava_token_expires_at = Column(DateTime, nullable=True)

    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    timezone = Column(String, default="America/New_York")
    units = Column(String, default="km")

    preferred_workout_days = Column(String, nullable=True)
    preferred_workout_time = Column(String, default="morning")
    available_equipment = Column(String, nullable=True)
    injury_history = Column(String, nullable=True)
    sleep_hours_target = Column(Float, nullable=True)

    min_recovery_threshold = Column(Float, default=30.0)
    low_hrv_threshold_ms = Column(Float, default=20.0)

    whoop_user_id = Column(String, nullable=True)
    whoop_access_token = Column(String, nullable=True)

    tenant_id = Column(String, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    training_plans = relationship(
        "TrainingPlan", back_populates="user", cascade="all, delete-orphan"
    )
    completed_workouts = relationship(
        "CompletedWorkout", back_populates="user", cascade="all, delete-orphan"
    )
