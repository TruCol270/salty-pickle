from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import (
    User,
    TrainingPlan,
    PlannedWorkout,
    AdjustmentLog,
    AdjustmentType,
    AdjustmentAgent,
    PlanStatus,
)
from app.services.plan_engine import PlanEngineService
from app.services.calendar_sync import CalendarSyncService


class WorkoutAdjustmentAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_engine = PlanEngineService(db)
        self.calendar_sync = CalendarSyncService(db)

    async def detect_missed_workouts(self, user: User) -> list[PlannedWorkout]:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        result = await self.db.execute(
            select(PlannedWorkout)
            .join(TrainingPlan)
            .where(
                and_(
                    TrainingPlan.user_id == user.id,
                    TrainingPlan.status == PlanStatus.ACTIVE,
                    PlannedWorkout.scheduled_date >= yesterday,
                    PlannedWorkout.scheduled_date < datetime.utcnow(),
                    PlannedWorkout.completed_workout.is_(None),
                )
            )
        )
        return result.scalars().all()

    async def detect_low_recovery(self, user: User) -> bool:
        return False

    async def adjust_for_missed_workout(
        self,
        user: User,
        workout: PlannedWorkout,
    ) -> dict:
        plan = workout.plan

        upcoming = await self.plan_engine.get_upcoming_workouts(plan.id, days=14)

        old_date = workout.scheduled_date
        new_date = old_date + timedelta(days=1)

        while new_date < plan.end_date:
            conflict = any(
                w.scheduled_date
                and w.scheduled_date.date() == new_date.date()
                and w.id != workout.id
                for w in upcoming
            )

            if not conflict:
                break

            new_date += timedelta(days=1)

        old_snapshot = await self.plan_engine.get_plan_snapshot(plan.id)

        workout.scheduled_date = new_date
        workout.notes = (
            workout.notes or ""
        ) + f"\n[Moved from {old_date.strftime('%Y-%m-%d')}]"

        adjustment = AdjustmentLog(
            workout_id=None,
            plan_id=plan.id,
            adjustment_type=AdjustmentType.DEFER,
            agent=AdjustmentAgent.RULE,
            trigger="missed",
            reason=f"Workout missed on {old_date.strftime('%Y-%m-%d')}. Shifted to {new_date.strftime('%Y-%m-%d')}",
            old_plan_snapshot=old_snapshot,
            new_plan_snapshot=await self.plan_engine.get_plan_snapshot(plan.id),
            applied="true",
            applied_at=datetime.utcnow(),
        )
        self.db.add(adjustment)

        if user.google_access_token:
            await self.calendar_sync.update_calendar_event(user, workout)

        await self.db.commit()

        return {
            "adjustment_id": adjustment.id,
            "adjustment_type": AdjustmentType.DEFER,
            "workout_id": workout.id,
            "old_date": old_date,
            "new_date": new_date,
            "message": f"Workout moved from {old_date.strftime('%b %d')} to {new_date.strftime('%b %d')}",
        }

    async def adjust_for_low_recovery(
        self,
        user: User,
        workout: PlannedWorkout,
    ) -> dict:
        high_intensity_types = ["tempo", "interval", "race"]

        if workout.workout_type.lower() not in high_intensity_types:
            return None

        old_type = workout.workout_type
        workout.workout_type = "recovery"

        workout.target_pace_min_per_km = None
        workout.notes = (
            workout.notes or ""
        ) + f"\n[Downgraded from {old_type} due to low recovery]"

        old_snapshot = await self.plan_engine.get_plan_snapshot(workout.plan_id)

        adjustment = AdjustmentLog(
            workout_id=None,
            plan_id=workout.plan_id,
            adjustment_type=AdjustmentType.MODIFY,
            agent=AdjustmentAgent.RULE,
            trigger="low_recovery",
            reason=f"Recovery score below threshold. Changed {old_type} to recovery.",
            old_plan_snapshot=old_snapshot,
            new_plan_snapshot=await self.plan_engine.get_plan_snapshot(workout.plan_id),
            applied="true",
            applied_at=datetime.utcnow(),
        )
        self.db.add(adjustment)

        if user.google_access_token:
            await self.calendar_sync.update_calendar_event(user, workout)

        await self.db.commit()

        return {
            "adjustment_id": adjustment.id,
            "adjustment_type": AdjustmentType.MODIFY,
            "workout_id": workout.id,
            "old_type": old_type,
            "new_type": "recovery",
            "message": f"Today's {old_type} replaced with easy recovery due to low recovery.",
        }

    async def run_daily_adjustments(self, user: User) -> list[dict]:
        adjustments = []

        missed = await self.detect_missed_workouts(user)
        for workout in missed:
            result = await self.adjust_for_missed_workout(user, workout)
            if result:
                adjustments.append(result)

        if await self.detect_low_recovery(user):
            active_plan = await self.plan_engine.get_active_plan(user.id)
            if active_plan:
                today = datetime.utcnow().date()
                for workout in active_plan.planned_workouts:
                    if (
                        workout.scheduled_date
                        and workout.scheduled_date.date() == today
                    ):
                        result = await self.adjust_for_low_recovery(user, workout)
                        if result:
                            adjustments.append(result)

        return adjustments
