from datetime import datetime, timedelta
from typing import Optional
import json

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, TrainingPlan, PlannedWorkout, PlanStatus
from app.services.plan_engine import PlanEngineService
from app.services.calendar_sync import CalendarSyncService
from app.services.workout_sync import WorkoutSyncService
from app.config import get_settings

settings = get_settings()


class PlanGeneratorAgent:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_engine = PlanEngineService(db)
        self.calendar_sync = CalendarSyncService(db)
        self.workout_sync = WorkoutSyncService(db)
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def analyze_strava_history(self, user: User, months: int = 6) -> dict:
        """Analyze user's Strava history to determine fitness level."""
        result = await self.db.execute(
            select(PlannedWorkout).where(PlannedWorkout.id == 0)
        )

        from app.models import CompletedWorkout

        cutoff = datetime.utcnow() - timedelta(days=months * 30)

        result = await self.db.execute(
            select(CompletedWorkout).where(
                CompletedWorkout.user_id == user.id,
                CompletedWorkout.start_time >= cutoff,
            )
        )
        workouts = result.scalars().all()

        if not workouts:
            return {
                "total_workouts": 0,
                "total_distance_km": 0,
                "average_heart_rate": None,
                "fitness_level": "unknown",
            }

        total_distance = sum(w.actual_distance_km or 0 for w in workouts)
        total_duration = sum(w.actual_duration_seconds or 0 for w in workouts)
        avg_hr = sum(
            w.average_heart_rate or 0 for w in workouts if w.average_heart_rate
        )
        hr_count = sum(1 for w in workouts if w.average_heart_rate)

        weekly_avg_km = total_distance / months
        avg_pace = (total_duration / 60) / total_distance if total_distance > 0 else 0

        if weekly_avg_km > 80:
            fitness_level = "elite"
        elif weekly_avg_km > 50:
            fitness_level = "advanced"
        elif weekly_avg_km > 25:
            fitness_level = "intermediate"
        else:
            fitness_level = "beginner"

        return {
            "total_workouts": len(workouts),
            "total_distance_km": round(total_distance, 1),
            "weekly_avg_km": round(weekly_avg_km, 1),
            "average_pace_min_per_km": round(avg_pace, 2) if avg_pace > 0 else None,
            "average_heart_rate": round(avg_hr / hr_count, 1) if hr_count > 0 else None,
            "fitness_level": fitness_level,
        }

    async def generate_training_plan(
        self,
        user: User,
        race_name: str,
        race_date: datetime,
        race_distance_km: float,
        current_fitness_level: str,
        weekly_mileage_km: float,
        years_experience: str,
        preferred_days: list[int] = None,
        preferred_time: str = "morning",
    ) -> dict:
        """Generate a personalized training plan using LLM."""

        strava_analysis = await self.analyze_strava_history(user)

        days_until_race = (race_date - datetime.utcnow()).days
        weeks = days_until_race // 7

        if weeks < 8:
            base_mileage = min(weekly_mileage_km * 1.5, 100)
            long_run_max = 32
        elif weeks < 12:
            base_mileage = min(weekly_mileage_km * 1.75, 120)
            long_run_max = 40
        else:
            base_mileage = min(weekly_mileage_km * 2, 150)
            long_run_max = 50

        preferred_days = preferred_days or [1, 3, 5, 6]

        prompt = f"""Generate a {weeks}-week ultra running training plan for:
- Race: {race_name} ({race_distance_km}km)
- Race date: {race_date.strftime("%Y-%m-%d")}
- Current fitness level: {current_fitness_level}
- Weekly mileage: {weekly_mileage_km}km
- Years experience: {years_experience}
- Strava analysis: {json.dumps(strava_analysis)}
- Preferred workout days: {preferred_days} (0=Mon, 1=Tue, etc.)
- Preferred time: {preferred_time}
- Base mileage: {base_mileage}km/week
- Max long run: {long_run_max}km

Return a JSON array of weekly workouts with this structure:
{{
  "weeks": [
    {{
      "week": 1,
      "workouts": [
        {{"day": 0, "type": "easy_run", "distance_km": 8, "notes": "Easy recovery run"}},
        {{"day": 2, "type": "tempo_run", "distance_km": 10, "notes": "Tempo at threshold"}},
        {{"day": 5, "type": "long_run", "distance_km": 20, "notes": "Long slow distance"}}
      ]
    }}
  ]
}}

Make the plan progressive - start conservative and build intensity.
Include variety: easy runs, tempo runs, intervals, long runs, recovery days, rest days.
For ultra races, include back-to-back long runs in later weeks.
"""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert ultra running coach. Generate detailed, progressive training plans. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8000,
        )

        content = response.choices[0].message.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            plan_data = json.loads(content)
        except json.JSONDecodeError:
            plan_data = {"weeks": []}
            for i in range(1, min(weeks + 1, 20)):
                plan_data["weeks"].append(
                    {
                        "week": i,
                        "workouts": [
                            {
                                "day": 0 if 0 in preferred_days else 1,
                                "type": "easy_run",
                                "distance_km": base_mileage * 0.3,
                                "notes": "Easy run",
                            },
                            {
                                "day": 2 if 2 in preferred_days else 3,
                                "type": "tempo_run",
                                "distance_km": base_mileage * 0.35,
                                "notes": "Tempo run",
                            },
                            {
                                "day": 5 if 5 in preferred_days else 6,
                                "type": "long_run",
                                "distance_km": min(base_mileage * 0.5, long_run_max),
                                "notes": "Long run",
                            },
                        ],
                    }
                )

        start_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        plan = await self.plan_engine.create_plan(
            user_id=user.id,
            name=f"{race_name} Training",
            start_date=start_date,
            end_date=race_date,
            goal_race_name=race_name,
            goal_race_date=race_date,
            goal_distance_km=race_distance_km,
        )

        week_offset = 0
        for week_data in plan_data.get("weeks", []):
            week_num = week_data.get("week", week_offset + 1)

            for workout_data in week_data.get("workouts", []):
                day_of_week = workout_data.get("day", 0)
                scheduled_date = start_date + timedelta(
                    weeks=week_offset, days=day_of_week
                )

                if scheduled_date >= race_date:
                    continue

                workout = PlannedWorkout(
                    plan_id=plan.id,
                    week_number=week_num,
                    day_of_week=day_of_week,
                    scheduled_date=scheduled_date,
                    workout_type=workout_data.get("type", "easy_run"),
                    target_distance_km=workout_data.get("distance_km"),
                    target_duration_minutes=workout_data.get("duration_minutes"),
                    notes=workout_data.get("notes"),
                    flexible=True,
                )
                self.db.add(workout)

        await self.db.commit()

        plan_result = await self.db.execute(
            select(TrainingPlan).where(TrainingPlan.id == plan.id)
        )
        plan = plan_result.scalar_one_or_none()

        if user.google_access_token:
            try:
                await self.calendar_sync.sync_plan_to_calendar(user, plan.id)
            except Exception as e:
                print(f"Failed to sync to calendar: {e}")

        return {
            "plan_id": plan.id,
            "weeks": len(plan_data.get("weeks", [])),
            "strava_analysis": strava_analysis,
        }
