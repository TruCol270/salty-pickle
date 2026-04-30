from datetime import datetime, timedelta
from typing import Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import (
    User,
    CompletedWorkout,
    PlannedWorkout,
    WorkoutSource,
    StravaSyncRun,
    SyncRunStatus,
)
from app.services.strava import StravaService


class WorkoutSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_from_strava(
        self, user: User, after: Optional[datetime] = None
    ) -> list[CompletedWorkout]:
        sync_run = StravaSyncRun(
            user_id=user.id,
            status=SyncRunStatus.STARTED,
            started_at=datetime.utcnow(),
            after_cursor=after,
        )
        self.db.add(sync_run)
        await self.db.flush()

        service = StravaService(self.db)
        try:
            user = await service.refresh_token_if_needed(user)

            activities = await service.get_activities(
                access_token=user.strava_access_token,
                after=after,
            )
            sync_run.activities_fetched = len(activities)

            synced = []
            for activity in activities:
                result = await self.db.execute(
                    select(CompletedWorkout).where(
                        and_(
                            CompletedWorkout.user_id == user.id,
                            CompletedWorkout.source_id == str(activity["id"]),
                        )
                    )
                )
                if result.scalar_one_or_none():
                    continue

                start_time = datetime.fromisoformat(
                    activity["start_date"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                end_time = datetime.fromisoformat(
                    activity["start_date_local"].replace("Z", "+00:00")
                ).replace(tzinfo=None) + timedelta(seconds=activity.get("elapsed_time", 0))

                workout = CompletedWorkout(
                    user_id=user.id,
                    source=WorkoutSource.STRAVA,
                    source_id=str(activity["id"]),
                    start_time=start_time,
                    end_time=end_time,
                    actual_distance_km=activity.get("distance", 0) / 1000,
                    actual_duration_seconds=activity.get("elapsed_time"),
                    actual_elevation_m=activity.get("total_elevation_gain"),
                    average_heart_rate=activity.get("average_heartrate"),
                    max_heart_rate=activity.get("max_heartrate"),
                    raw_data=json.dumps(activity),
                )

                self.db.add(workout)
                synced.append(workout)

            sync_run.status = SyncRunStatus.SUCCESS
            sync_run.finished_at = datetime.utcnow()
            sync_run.workouts_created = len(synced)
            await self.db.commit()
            return synced
        except Exception as exc:
            await self.db.rollback()
            sync_run.status = SyncRunStatus.FAILED
            sync_run.error_message = str(exc)
            sync_run.finished_at = datetime.utcnow()
            self.db.add(sync_run)
            await self.db.commit()
            raise

    async def calculate_performance_score(self, workout: CompletedWorkout) -> float:
        if not workout.planned_workout_id:
            return None

        planned = workout.planned_workout

        if planned.target_distance_km and workout.actual_distance_km:
            distance_ratio = min(
                workout.actual_distance_km / planned.target_distance_km, 1.5
            )
            distance_score = max(0, 100 - abs(1 - distance_ratio) * 100) * 0.4
        else:
            distance_score = 40

        if planned.target_pace_min_per_km and workout.actual_pace_min_per_km:
            pace_ratio = planned.target_pace_min_per_km / workout.actual_pace_min_per_km
            pace_score = max(0, 100 - abs(1 - pace_ratio) * 100) * 0.3
        else:
            pace_score = 30

        completion_score = 30 if workout.actual_duration_seconds else 0

        return distance_score + pace_score + completion_score
