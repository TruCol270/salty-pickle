from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, false

from app.models import User, TrainingPlan, PlannedWorkout, CompletedWorkout, PlanStatus
from app.services.google_calendar import GoogleCalendarService
from app.services.whoop import WhoopService


class PerformanceAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def match_strava_to_planned(self, user: User) -> list[dict]:
        """Match completed Strava workouts to planned workouts."""

        result = await self.db.execute(
            select(TrainingPlan).where(
                and_(
                    TrainingPlan.user_id == user.id,
                    TrainingPlan.status == PlanStatus.ACTIVE,
                )
            )
        )
        plans = result.scalars().all()

        matches = []

        for plan in plans:
            result = await self.db.execute(
                select(PlannedWorkout).where(
                    and_(
                        PlannedWorkout.plan_id == plan.id,
                        PlannedWorkout.completed == "false",
                    )
                )
            )
            planned_workouts = result.scalars().all()

            result = await self.db.execute(
                select(CompletedWorkout).where(
                    CompletedWorkout.user_id == user.id,
                    CompletedWorkout.start_time >= plan.start_date,
                )
            )
            completed_workouts = result.scalars().all()

            for planned in planned_workouts:
                if not planned.scheduled_date:
                    continue

                best_match = None
                best_diff = float("inf")

                for completed in completed_workouts:
                    if completed.planned_workout_id:
                        continue

                    planned_date = (
                        planned.scheduled_date.date()
                        if planned.scheduled_date
                        else None
                    )
                    completed_date = (
                        completed.start_time.date() if completed.start_time else None
                    )

                    if not planned_date or not completed_date:
                        continue

                    diff_days = abs((planned_date - completed_date).days)

                    if diff_days <= 1:
                        if planned.target_distance_km and completed.actual_distance_km:
                            distance_diff = (
                                abs(
                                    planned.target_distance_km
                                    - completed.actual_distance_km
                                )
                                / planned.target_distance_km
                            )
                        else:
                            distance_diff = 0

                        if distance_diff < 0.3 and diff_days < best_diff:
                            best_match = completed
                            best_diff = diff_days

                if best_match:
                    matches.append(
                        {
                            "planned": planned,
                            "completed": best_match,
                            "planned_date": planned.scheduled_date,
                            "completed_date": best_match.start_time,
                        }
                    )

        return matches

    async def calculate_performance_score(
        self,
        planned: PlannedWorkout,
        completed: CompletedWorkout,
    ) -> float:
        """Calculate how well the workout matched the plan."""
        scores = []

        if planned.target_distance_km and completed.actual_distance_km:
            distance_ratio = completed.actual_distance_km / planned.target_distance_km
            if distance_ratio >= 0.9 and distance_ratio <= 1.1:
                distance_score = 100
            elif distance_ratio >= 0.75:
                distance_score = 100 - abs(1 - distance_ratio) * 100
            else:
                distance_score = max(0, 50 - (0.75 - distance_ratio) * 200)
            scores.append(distance_score * 0.4)

        if planned.target_duration_minutes and completed.actual_duration_seconds:
            planned_duration = planned.target_duration_minutes
            actual_duration = completed.actual_duration_seconds / 60
            duration_ratio = actual_duration / planned_duration
            if duration_ratio >= 0.9 and duration_ratio <= 1.1:
                duration_score = 100
            else:
                duration_score = max(0, 100 - abs(1 - duration_ratio) * 100)
            scores.append(duration_score * 0.3)

        if completed.actual_duration_seconds:
            scores.append(30)

        return sum(scores) if scores else None

    async def adjust_plan_based_on_performance(
        self, user: User, matches: list[dict]
    ) -> list[dict]:
        """Adjust next week's workouts based on recent performance."""
        if len(matches) < 3:
            return []

        total_score = 0
        scored_count = 0

        for match in matches[-7:]:
            planned = match["planned"]
            completed = match["completed"]
            score = await self.calculate_performance_score(planned, completed)
            if score:
                total_score += score
                scored_count += 1

        if scored_count == 0:
            return []

        avg_score = total_score / scored_count

        adjustments = []

        result = await self.db.execute(
            select(TrainingPlan).where(
                and_(
                    TrainingPlan.user_id == user.id,
                    TrainingPlan.status == PlanStatus.ACTIVE,
                )
            )
        )
        plans = result.scalars().all()

        for plan in plans:
            result = await self.db.execute(
                select(PlannedWorkout)
                .where(
                    and_(
                        PlannedWorkout.plan_id == plan.id,
                        PlannedWorkout.completed == "false",
                        PlannedWorkout.scheduled_date >= datetime.utcnow(),
                    )
                )
                .order_by(PlannedWorkout.scheduled_date)
            )
            upcoming = result.scalars().all()

            if avg_score >= 85:
                adjustment_type = "increase"
                message = f"Great performance ({avg_score:.0f}%)! Adding 10% more distance next week."
                adjustment_factor = 1.10
            elif avg_score >= 70:
                adjustment_type = "maintain"
                message = f"Good performance ({avg_score:.0f}%). Keeping plan as is."
                adjustment_factor = 1.0
            elif avg_score >= 50:
                adjustment_type = "decrease"
                message = f"Tough week ({avg_score:.0f}%). Reducing next week by 15% for recovery."
                adjustment_factor = 0.85
            else:
                adjustment_type = "recovery"
                message = f"Struggled this week ({avg_score:.0f}%). Switching to recovery week."
                adjustment_factor = 0.5

            for workout in upcoming[:3]:
                if adjustment_type == "increase":
                    if workout.target_distance_km:
                        workout.target_distance_km = round(
                            workout.target_distance_km * adjustment_factor, 1
                        )
                elif adjustment_type == "decrease" or adjustment_type == "recovery":
                    if workout.target_distance_km:
                        workout.target_distance_km = round(
                            workout.target_distance_km * adjustment_factor, 1
                        )
                    if adjustment_type == "recovery":
                        workout.workout_type = "recovery"
                        workout.target_pace_min_per_km = None

                adjustments.append(
                    {
                        "workout_id": workout.id,
                        "type": adjustment_type,
                        "message": message,
                    }
                )

            if adjustments:
                await self.db.commit()

        return adjustments[:5]

    async def run_daily_performance_check(self, user: User) -> dict:
        """Main job: sync, match, and adjust."""
        from app.services.workout_sync import WorkoutSyncService

        sync_service = WorkoutSyncService(self.db)
        synced = await sync_service.sync_from_strava(user)

        matches = await self.match_strava_to_planned(user)

        for match in matches:
            planned = match["planned"]
            completed = match["completed"]

            planned.completed_workout = completed
            planned.completed = "true"

            score = await self.calculate_performance_score(planned, completed)
            if score:
                planned.notes = (
                    planned.notes or ""
                ) + f"\n[Completed! Score: {score:.0f}%]"

        await self.db.commit()

        adjustments = await self.adjust_plan_based_on_performance(user, matches)

        whoop_recovery = None
        if user.whoop_access_token:
            try:
                whoop_service = WhoopService(self.db)
                whoop_recovery = await whoop_service.get_latest_recovery(user)
            except Exception as e:
                print(f"Failed to get Whoop recovery: {e}")

        recovery_recommendation = "maintain"
        if whoop_recovery:
            whoop_service = WhoopService(self.db)
            recovery_recommendation = await whoop_service.get_recovery_recommendation(
                whoop_recovery
            )

        return {
            "synced": len(synced),
            "matched": len(matches),
            "adjustments": len(adjustments),
            "whoop_recovery": whoop_recovery,
            "recovery_recommendation": recovery_recommendation,
            "details": adjustments,
        }
