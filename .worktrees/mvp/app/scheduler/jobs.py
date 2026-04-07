from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.services.workout_sync import WorkoutSyncService
from app.services.performance_analyzer import PerformanceAnalyzer
from app.agents.adjustment_agent import WorkoutAdjustmentAgent
from app.models import User


scheduler = AsyncIOScheduler()


async def sync_workouts_job():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            if not user.strava_access_token:
                continue

            try:
                service = WorkoutSyncService(db)
                after = datetime.utcnow() - timedelta(hours=24)
                synced = await service.sync_from_strava(user, after=after)
                print(f"Synced {len(synced)} workouts for user {user.id}")
            except Exception as e:
                print(f"Failed to sync workouts for user {user.id}: {e}")


async def run_adjustments_job():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                agent = WorkoutAdjustmentAgent(db)
                adjustments = await agent.run_daily_adjustments(user)

                if adjustments:
                    print(f"Made {len(adjustments)} adjustments for user {user.id}")
                    for adj in adjustments:
                        print(f"  - {adj['message']}")
            except Exception as e:
                print(f"Failed to run adjustments for user {user.id}: {e}")


async def performance_check_job():
    """Cross-reference Strava with planned workouts and adjust plan."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            if not user.strava_access_token:
                continue

            try:
                analyzer = PerformanceAnalyzer(db)
                result = await analyzer.run_daily_performance_check(user)

                print(f"Performance check for user {user.id}:")
                print(f"  - Synced: {result['synced']} new workouts")
                print(f"  - Matched: {result['matched']} completed workouts to plan")
                print(f"  - Adjustments: {result['adjustments']} plan changes")

                for adj in result.get("details", []):
                    print(f"    - {adj['type']}: {adj['message']}")
            except Exception as e:
                print(f"Failed performance check for user {user.id}: {e}")


def setup_scheduler():
    scheduler.add_job(
        sync_workouts_job,
        CronTrigger(hour="*/6"),
        id="sync_workouts",
        replace_existing=True,
    )

    scheduler.add_job(
        run_adjustments_job,
        CronTrigger(hour=6, minute=0),
        id="run_adjustments",
        replace_existing=True,
    )

    scheduler.add_job(
        performance_check_job,
        CronTrigger(hour=6, minute=30),
        id="performance_check",
        replace_existing=True,
    )

    scheduler.start()
    print("Scheduler started")


def shutdown_scheduler():
    scheduler.shutdown()
