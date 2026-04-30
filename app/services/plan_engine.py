from datetime import datetime, timedelta
from typing import Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models import TrainingPlan, PlannedWorkout, PlanStatus


class PlanEngineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_plan(
        self,
        user_id: int,
        name: str,
        start_date: datetime,
        end_date: datetime,
        workouts: list[dict],
        goal_race_name: Optional[str] = None,
        goal_race_date: Optional[datetime] = None,
        goal_distance_km: Optional[float] = None,
    ) -> TrainingPlan:
        plan = TrainingPlan(
            user_id=user_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            goal_race_name=goal_race_name,
            goal_race_date=goal_race_date,
            goal_distance_km=goal_distance_km,
            status=PlanStatus.ACTIVE,
            current_week_number=1,
        )
        self.db.add(plan)
        await self.db.flush()

        for workout_data in workouts:
            scheduled_date = start_date + timedelta(
                weeks=workout_data["week_number"] - 1,
                days=workout_data["day_of_week"],
            )

            workout = PlannedWorkout(
                plan_id=plan.id,
                week_number=workout_data["week_number"],
                day_of_week=workout_data["day_of_week"],
                workout_type=workout_data["workout_type"],
                target_distance_km=workout_data.get("target_distance_km"),
                target_duration_minutes=workout_data.get("target_duration_minutes"),
                target_pace_min_per_km=workout_data.get("target_pace_min_per_km"),
                target_elevation_m=workout_data.get("target_elevation_m"),
                flexible=str(workout_data.get("flexible", True)).lower(),
                notes=workout_data.get("notes"),
                scheduled_date=scheduled_date,
            )
            self.db.add(workout)

        await self.db.commit()

        result = await self.db.execute(
            select(TrainingPlan)
            .options(selectinload(TrainingPlan.planned_workouts))
            .where(TrainingPlan.id == plan.id)
        )
        return result.scalar_one()

    async def get_active_plan(self, user_id: int) -> Optional[TrainingPlan]:
        result = await self.db.execute(
            select(TrainingPlan)
            .options(selectinload(TrainingPlan.planned_workouts))
            .where(
                and_(
                    TrainingPlan.user_id == user_id,
                    TrainingPlan.status == PlanStatus.ACTIVE,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_plan(
        self,
        plan_id: int,
        **updates,
    ) -> TrainingPlan:
        result = await self.db.execute(
            select(TrainingPlan)
            .options(selectinload(TrainingPlan.planned_workouts))
            .where(TrainingPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError("Plan not found")

        for key, value in updates.items():
            if hasattr(plan, key) and value is not None:
                setattr(plan, key, value)

        await self.db.commit()
        return plan

    async def get_upcoming_workouts(
        self,
        plan_id: int,
        days: int = 7,
    ) -> list[PlannedWorkout]:
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)

        result = await self.db.execute(
            select(PlannedWorkout)
            .where(
                and_(
                    PlannedWorkout.plan_id == plan_id,
                    PlannedWorkout.scheduled_date >= now,
                    PlannedWorkout.scheduled_date <= end_date,
                )
            )
            .order_by(PlannedWorkout.scheduled_date)
        )
        return result.scalars().all()

    async def get_plan_snapshot(self, plan_id: int) -> str:
        result = await self.db.execute(
            select(TrainingPlan)
            .options(selectinload(TrainingPlan.planned_workouts))
            .where(TrainingPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        return json.dumps(
            {
                "plan_id": plan.id,
                "name": plan.name,
                "status": plan.status,
                "current_week": plan.current_week_number,
                "workouts": [
                    {
                        "id": w.id,
                        "week": w.week_number,
                        "day": w.day_of_week,
                        "type": w.workout_type,
                        "distance": w.target_distance_km,
                        "date": w.scheduled_date.isoformat()
                        if w.scheduled_date
                        else None,
                    }
                    for w in plan.planned_workouts
                ],
            }
        )
