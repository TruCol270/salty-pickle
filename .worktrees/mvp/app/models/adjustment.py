from datetime import datetime
from sqlalchemy import Boolean, Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class AdjustmentType:
    SKIP = "skip"
    MODIFY = "modify"
    SWAP = "swap"
    DEFER = "defer"


class AdjustmentAgent:
    RULE = "rule"
    LLM = "llm"


class AdjustmentLog(Base):
    __tablename__ = "adjustment_logs"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("completed_workouts.id"), nullable=True)
    plan_id = Column(
        Integer, ForeignKey("training_plans.id"), nullable=False, index=True
    )

    adjustment_type = Column(String, nullable=False)
    agent = Column(String, default=AdjustmentAgent.RULE)

    trigger = Column(String, nullable=True)
    reason = Column(Text, nullable=True)

    old_plan_snapshot = Column(Text, nullable=True)
    new_plan_snapshot = Column(Text, nullable=True)

    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    workout = relationship("CompletedWorkout", back_populates="adjustments")
