from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class WorkoutSource:
    STRAVA = "strava"
    WHOOP = "whoop"
    COROS = "coros"
    MANUAL = "manual"


class CompletedWorkout(Base):
    __tablename__ = "completed_workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    planned_workout_id = Column(
        Integer, ForeignKey("planned_workouts.id"), nullable=True
    )

    source = Column(String, default=WorkoutSource.STRAVA)
    source_id = Column(String, nullable=True)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)

    actual_distance_km = Column(Float, nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)
    actual_pace_min_per_km = Column(Float, nullable=True)
    actual_elevation_m = Column(Float, nullable=True)
    average_heart_rate = Column(Float, nullable=True)
    max_heart_rate = Column(Float, nullable=True)
    average_cadence = Column(Float, nullable=True)

    performance_score = Column(Float, nullable=True)
    perceived_effort = Column(Integer, nullable=True)

    workout_type = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    raw_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="completed_workouts")
    planned_workout = relationship("PlannedWorkout", back_populates="completed_workout")
    adjustments = relationship("AdjustmentLog", back_populates="workout")
