from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import CompletedWorkout, TrainingPlan


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_performance_trends(
        self,
        user_id: int,
        days: int = 30,
    ) -> dict:
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(CompletedWorkout)
            .where(
                and_(
                    CompletedWorkout.user_id == user_id,
                    CompletedWorkout.start_time >= start_date,
                )
            )
            .order_by(CompletedWorkout.start_time)
        )
        workouts = result.scalars().all()

        if not workouts:
            return {
                "total_workouts": 0,
                "total_distance_km": 0,
                "total_duration_seconds": 0,
                "average_pace": None,
                "workouts_by_type": {},
                "weekly_distances": [],
            }

        total_distance = sum(w.actual_distance_km or 0 for w in workouts)
        total_duration = sum(w.actual_duration_seconds or 0 for w in workouts)

        workouts_with_pace = [w for w in workouts if w.actual_pace_min_per_km]
        avg_pace = (
            sum(w.actual_pace_min_per_km for w in workouts_with_pace)
            / len(workouts_with_pace)
            if workouts_with_pace
            else None
        )

        by_type = {}
        for w in workouts:
            workout_type = w.workout_type or "unknown"
            by_type[workout_type] = by_type.get(workout_type, 0) + 1

        weekly = {}
        for w in workouts:
            week_start = w.start_time - timedelta(days=w.start_time.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            weekly[week_key] = weekly.get(week_key, 0) + (w.actual_distance_km or 0)

        weekly_distances = [
            {"week": k, "distance_km": round(v, 1)} for k, v in sorted(weekly.items())
        ]

        return {
            "total_workouts": len(workouts),
            "total_distance_km": round(total_distance, 1),
            "total_duration_seconds": total_duration,
            "average_pace": round(avg_pace, 2) if avg_pace else None,
            "workouts_by_type": by_type,
            "weekly_distances": weekly_distances,
        }

    async def get_plan_progress(
        self,
        plan_id: int,
    ) -> dict:
        result = await self.db.execute(
            select(TrainingPlan).where(TrainingPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            return None

        total_workouts = len(plan.planned_workouts)
        completed = sum(1 for w in plan.planned_workouts if w.completed_workout)

        total_distance = sum(w.target_distance_km or 0 for w in plan.planned_workouts)
        completed_distance = sum(
            w.completed_workout.actual_distance_km or 0
            for w in plan.planned_workouts
            if w.completed_workout
        )

        now = datetime.utcnow()
        if plan.start_date <= now <= plan.end_date:
            days_elapsed = (now - plan.start_date).days
            current_week = (days_elapsed // 7) + 1
        else:
            current_week = plan.current_week_number

        return {
            "plan_id": plan.id,
            "plan_name": plan.name,
            "status": plan.status,
            "current_week": current_week,
            "total_weeks": ((plan.end_date - plan.start_date).days // 7) + 1,
            "completed_workouts": completed,
            "total_workouts": total_workouts,
            "completion_percentage": round(
                (completed / total_workouts * 100) if total_workouts else 0, 1
            ),
            "planned_distance_km": round(total_distance, 1),
            "completed_distance_km": round(completed_distance, 1),
            "distance_completion_percentage": round(
                (completed_distance / total_distance * 100) if total_distance else 0, 1
            ),
        }
