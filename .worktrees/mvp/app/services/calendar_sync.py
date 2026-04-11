from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import User, TrainingPlan, PlannedWorkout
from app.services.google_calendar import GoogleCalendarService
from app.services.plan_engine import PlanEngineService
from app.schemas.calendar import CalendarEventResponse


class CalendarSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calendar_service = GoogleCalendarService(db)
        self.plan_engine = PlanEngineService(db)

    def _transform_google_event(self, event: dict) -> CalendarEventResponse:
        return CalendarEventResponse(
            id=event.get("id", ""),
            summary=event.get("summary", ""),
            description=event.get("description"),
            start_time=datetime.fromisoformat(
                event["start"]["dateTime"].replace("Z", "+00:00")
            )
            if event.get("start", {}).get("dateTime")
            else datetime.utcnow(),
            end_time=datetime.fromisoformat(
                event["end"]["dateTime"].replace("Z", "+00:00")
            )
            if event.get("end", {}).get("dateTime")
            else datetime.utcnow(),
            location=event.get("location"),
        )

    async def sync_plan_to_calendar(
        self,
        user: User,
        plan_id: int,
    ) -> list[CalendarEventResponse]:
        result = await self.db.execute(
            select(TrainingPlan).where(
                and_(
                    TrainingPlan.id == plan_id,
                    TrainingPlan.user_id == user.id,
                )
            )
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError("Plan not found")

        workouts_result = await self.db.execute(
            select(PlannedWorkout).where(PlannedWorkout.plan_id == plan_id)
        )
        planned_workouts = workouts_result.scalars().all()

        synced = []
        for workout in planned_workouts:
            scheduled_date = workout.scheduled_date
            if not scheduled_date:
                # Compute from week/day offset
                day_offset = (workout.week_number - 1) * 7 + (workout.day_of_week - 1)
                scheduled_date = plan.start_date + timedelta(days=day_offset)
                workout.scheduled_date = scheduled_date

            duration_hours = 1
            if workout.workout_type == "long":
                duration_hours = 2 + (workout.target_distance_km or 0) / 10
            elif workout.workout_type in ["interval", "tempo"]:
                duration_hours = 1.5

            end_time = scheduled_date + timedelta(hours=duration_hours)

            distance_str = (
                f" {workout.target_distance_km:.1f}km"
                if workout.target_distance_km
                else ""
            )
            pace_str = (
                f" @ {workout.target_pace_min_per_km:.1f}/km"
                if workout.target_pace_min_per_km
                else ""
            )

            summary = f"Run: {workout.workout_type.title()}{distance_str}{pace_str}"
            description = f"Training plan: {plan.name}\n\n"

            if workout.notes:
                description += f"Notes: {workout.notes}\n\n"

            description += f"Workout ID: {workout.id}"

            try:
                event = await self.calendar_service.create_event(
                    user=user,
                    summary=summary,
                    description=description,
                    start_time=scheduled_date,
                    end_time=end_time,
                )

                workout.calendar_event_id = event["id"]
                synced.append(self._transform_google_event(event))
            except Exception as e:
                print(f"Failed to create calendar event: {e}")

        await self.db.commit()
        return synced

    async def update_calendar_event(
        self,
        user: User,
        workout: PlannedWorkout,
    ) -> Optional[dict]:
        if not workout.calendar_event_id:
            return None

        plan = workout.plan

        duration_hours = 1
        if workout.workout_type == "long":
            duration_hours = 2 + (workout.target_distance_km or 0) / 10

        end_time = workout.scheduled_date + timedelta(hours=duration_hours)

        distance_str = (
            f" {workout.target_distance_km:.1f}km" if workout.target_distance_km else ""
        )
        summary = f"🏃 {workout.workout_type.title()}{distance_str}"

        try:
            event = await self.calendar_service.update_event(
                user=user,
                event_id=workout.calendar_event_id,
                summary=summary,
                description=f"Updated workout from {plan.name}\nWorkout ID: {workout.id}",
                start_time=workout.scheduled_date,
                end_time=end_time,
            )
            return event
        except Exception as e:
            print(f"Failed to update calendar event: {e}")
            return None
