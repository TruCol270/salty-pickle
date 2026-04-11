import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.services.workout_sync import WorkoutSyncService
from app.services.performance_analyzer import PerformanceAnalyzer
from app.agents.adjustment_agent import WorkoutAdjustmentAgent
from app.models import User

logger = logging.getLogger(__name__)

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
                logger.info("Synced %d workouts for user %s", len(synced), user.id)
            except Exception:
                logger.exception("Failed to sync workouts for user %s", user.id)


async def run_adjustments_job():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                agent = WorkoutAdjustmentAgent(db)
                adjustments = await agent.run_daily_adjustments(user)

                if adjustments:
                    logger.info("Made %d adjustments for user %s", len(adjustments), user.id)
                    for adj in adjustments:
                        logger.info("  - %s", adj["message"])
            except Exception:
                logger.exception("Failed to run adjustments for user %s", user.id)


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

                logger.info("Performance check for user %s:", user.id)
                logger.info("  - Synced: %d new workouts", result["synced"])
                logger.info("  - Matched: %d completed workouts to plan", result["matched"])
                logger.info("  - Adjustments: %d plan changes", result["adjustments"])

                for adj in result.get("details", []):
                    logger.info("    - %s: %s", adj["type"], adj["message"])
            except Exception:
                logger.exception("Failed performance check for user %s", user.id)


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
    logger.info("Scheduler started")


def shutdown_scheduler():
    scheduler.shutdown()
