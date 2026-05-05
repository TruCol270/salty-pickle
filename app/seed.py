"""Idempotent beta data seed for local/staging PostgreSQL environments."""

import argparse
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    AnalyticsEvent,
    CompletedWorkout,
    PlanPerformanceSnapshot,
    PlannedWorkout,
    PlanStatus,
    ProviderWebhookEvent,
    TrainingPlan,
    User,
    WhoopRecoverySample,
    WorkoutSource,
)

BETA_EMAIL = "beta.runner@saltypickle.test"
BETA_TENANT_ID = "beta-seed"
BETA_PLAN_NAME = "Beta Half Marathon Build"
BETA_SOURCE_IDS = [
    "beta-seed-easy-5k",
    "beta-seed-tempo-8k",
    "beta-seed-long-14k",
]
BETA_WEBHOOK_EVENT_IDS = [
    "beta-seed-strava-activity-created",
    "beta-seed-whoop-recovery-updated",
]


async def _get_or_create_user(session: AsyncSession, email: str) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email)
        session.add(user)
        await session.flush()

    user.timezone = "America/Chicago"
    user.units = "km"
    user.preferred_workout_days = "Mon,Wed,Fri,Sun"
    user.preferred_workout_time = "morning"
    user.available_equipment = "Road shoes, heart-rate strap, treadmill"
    user.injury_history = "Mild calf tightness in prior build"
    user.sleep_hours_target = 8.0
    user.min_recovery_threshold = 35.0
    user.low_hrv_threshold_ms = 25.0
    user.tenant_id = BETA_TENANT_ID
    user.strava_athlete_id = "beta-seed-strava-athlete"
    user.google_calendar_id = "beta-seed-calendar"
    user.whoop_user_id = "beta-seed-whoop-user"
    user.updated_at = datetime.utcnow()
    return user


async def _get_or_create_plan(
    session: AsyncSession, user: User, now: datetime
) -> TrainingPlan:
    plan = await session.scalar(
        select(TrainingPlan).where(
            TrainingPlan.user_id == user.id,
            TrainingPlan.name == BETA_PLAN_NAME,
        )
    )
    if plan is None:
        plan = TrainingPlan(user_id=user.id, name=BETA_PLAN_NAME)
        session.add(plan)

    start = now.replace(hour=6, minute=0, second=0, microsecond=0)
    plan.description = (
        "Seeded beta plan for smoke-testing plan, workout, and analytics screens."
    )
    plan.start_date = start
    plan.end_date = start + timedelta(weeks=8)
    plan.goal_race_name = "Salty Pickle Spring Half"
    plan.goal_race_date = start + timedelta(weeks=8, days=6)
    plan.goal_distance_km = 21.1
    plan.goal_time_seconds = 7200
    plan.status = PlanStatus.ACTIVE
    plan.current_week_number = 2
    plan.updated_at = now
    await session.flush()
    return plan


def _planned_workouts(
    plan: TrainingPlan, start: datetime
) -> list[PlannedWorkout]:
    workouts = [
        (1, 1, "easy_run", 5.0, 35, 6.4, "Conversational effort with relaxed strides."),
        (1, 3, "tempo", 8.0, 48, 5.7, "Include 3 x 8 min at steady tempo."),
        (1, 6, "long_run", 12.0, 82, 6.8, "Keep the last 2 km controlled, not hard."),
        (2, 1, "recovery", 4.0, 30, 7.0, "Short recovery run after long-run day."),
        (2, 3, "intervals", 7.0, 46, 5.2, "6 x 400 m with full easy jog recoveries."),
        (2, 6, "long_run", 14.0, 96, 6.8, "Practice fueling at 40 minutes."),
    ]
    return [
        PlannedWorkout(
            plan_id=plan.id,
            week_number=week,
            day_of_week=day,
            workout_type=kind,
            target_distance_km=distance,
            target_duration_minutes=duration,
            target_pace_min_per_km=pace,
            flexible=True,
            notes=notes,
            scheduled_date=start + timedelta(days=(week - 1) * 7 + day - 1),
            completed=False,
        )
        for week, day, kind, distance, duration, pace, notes in workouts
    ]


def _completed_workouts(user: User, start: datetime) -> list[CompletedWorkout]:
    completed = [
        (
            "beta-seed-easy-5k",
            start - timedelta(days=6),
            5.1,
            1900,
            6.2,
            142,
            "easy_run",
        ),
        (
            "beta-seed-tempo-8k",
            start - timedelta(days=4),
            8.2,
            2820,
            5.7,
            158,
            "tempo",
        ),
        (
            "beta-seed-long-14k",
            start - timedelta(days=1),
            14.0,
            5700,
            6.8,
            149,
            "long_run",
        ),
    ]
    return [
        CompletedWorkout(
            user_id=user.id,
            source=WorkoutSource.MANUAL,
            source_id=source_id,
            start_time=started,
            end_time=started + timedelta(seconds=duration),
            actual_distance_km=distance,
            actual_duration_seconds=duration,
            actual_pace_min_per_km=pace,
            actual_elevation_m=55.0,
            average_heart_rate=heart_rate,
            max_heart_rate=heart_rate + 18,
            average_cadence=174.0,
            performance_score=88.0,
            perceived_effort=5,
            workout_type=kind,
            notes="Seeded beta workout.",
        )
        for source_id, started, distance, duration, pace, heart_rate, kind in completed
    ]


async def _replace_beta_rows(session: AsyncSession, user: User, plan: TrainingPlan) -> None:
    await session.execute(
        delete(AnalyticsEvent).where(
            AnalyticsEvent.user_id == user.id,
            AnalyticsEvent.source == "beta_seed",
        )
    )
    await session.execute(
        delete(PlanPerformanceSnapshot).where(
            PlanPerformanceSnapshot.user_id == user.id,
            PlanPerformanceSnapshot.plan_id == plan.id,
        )
    )
    await session.execute(
        delete(ProviderWebhookEvent).where(
            ProviderWebhookEvent.event_id.in_(BETA_WEBHOOK_EVENT_IDS)
        )
    )
    await session.execute(
        delete(WhoopRecoverySample).where(
            WhoopRecoverySample.user_id == user.id,
            WhoopRecoverySample.source == "beta_seed",
        )
    )
    await session.execute(
        delete(CompletedWorkout).where(
            CompletedWorkout.user_id == user.id,
            CompletedWorkout.source == WorkoutSource.MANUAL,
            CompletedWorkout.source_id.in_(BETA_SOURCE_IDS),
        )
    )
    await session.execute(
        delete(PlannedWorkout).where(PlannedWorkout.plan_id == plan.id)
    )
    await session.flush()


async def seed_beta(email: str = BETA_EMAIL) -> dict[str, int | str]:
    now = datetime.utcnow()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await _get_or_create_user(session, email)
            plan = await _get_or_create_plan(session, user, now)
            await _replace_beta_rows(session, user, plan)

            start = plan.start_date
            planned = _planned_workouts(plan, start)
            completed = _completed_workouts(user, start)
            session.add_all(planned)
            session.add_all(completed)
            session.add_all(
                [
                    WhoopRecoverySample(
                        user_id=user.id,
                        whoop_user_id=user.whoop_user_id,
                        source="beta_seed",
                        source_id="beta-seed-recovery-1",
                        cycle_id="beta-seed-cycle-1",
                        recovery_score=72,
                        resting_heart_rate=48,
                        hrv_rmssd_milli=61,
                        spo2_percentage=98.2,
                        skin_temp_celsius=33.4,
                        recorded_at=start - timedelta(hours=3),
                        payload={"fixture": "beta_seed"},
                    ),
                    ProviderWebhookEvent(
                        provider="strava",
                        event_type="activity.created",
                        provider_user_id=user.strava_athlete_id,
                        user_id=user.id,
                        event_id=BETA_WEBHOOK_EVENT_IDS[0],
                        received_at=now - timedelta(hours=5),
                        processed_at=now - timedelta(hours=4, minutes=59),
                        status="success",
                        payload={"fixture": "beta_seed"},
                    ),
                    ProviderWebhookEvent(
                        provider="whoop",
                        event_type="recovery.updated",
                        provider_user_id=user.whoop_user_id,
                        user_id=user.id,
                        event_id=BETA_WEBHOOK_EVENT_IDS[1],
                        received_at=now - timedelta(hours=4),
                        processed_at=now - timedelta(hours=3, minutes=59),
                        status="success",
                        payload={"fixture": "beta_seed"},
                    ),
                    AnalyticsEvent(
                        user_id=user.id,
                        plan_id=plan.id,
                        event_name="beta_seed_loaded",
                        source="beta_seed",
                        occurred_at=now,
                        payload={
                            "planned_workouts": len(planned),
                            "completed_workouts": len(completed),
                        },
                    ),
                    PlanPerformanceSnapshot(
                        user_id=user.id,
                        plan_id=plan.id,
                        snapshot_at=now,
                        matched_workouts=len(completed),
                        average_score=88.0,
                        adjustments_count=0,
                        recovery_recommendation="Proceed with planned workout.",
                        metadata_json={"fixture": "beta_seed"},
                    ),
                ]
            )
            await session.flush()
            return {
                "user_id": user.id,
                "plan_id": plan.id,
                "planned_workouts": len(planned),
                "completed_workouts": len(completed),
                "email": user.email or email,
            }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed beta data into the configured database."
    )
    parser.add_argument(
        "--email",
        default=BETA_EMAIL,
        help=f"Beta user email to create/update. Defaults to {BETA_EMAIL}.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    result = await seed_beta(email=args.email)
    print(
        "Seeded beta data: "
        f"user_id={result['user_id']} plan_id={result['plan_id']} "
        f"planned_workouts={result['planned_workouts']} "
        f"completed_workouts={result['completed_workouts']} "
        f"email={result['email']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
