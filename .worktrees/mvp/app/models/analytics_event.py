from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String

from app.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=True, index=True)

    event_name = Column(String, nullable=False, index=True)
    source = Column(String, nullable=True, index=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    payload = Column(JSON, nullable=True)


class PlanPerformanceSnapshot(Base):
    __tablename__ = "plan_performance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=False, index=True)

    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    matched_workouts = Column(Integer, default=0, nullable=False)
    average_score = Column(Float, nullable=True)
    adjustments_count = Column(Integer, default=0, nullable=False)
    recovery_recommendation = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
