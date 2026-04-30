import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, delete, update

from app.database import AsyncSessionLocal
from app.config import get_settings
from app.services.workout_sync import WorkoutSyncService
from app.services.performance_analyzer import PerformanceAnalyzer
from app.agents.adjustment_agent import WorkoutAdjustmentAgent
from app.models import User, ProviderWebhookEvent, CompletedWorkout

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
settings = get_settings()


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
            except Exception as e:
                logger.exception("Failed to sync workouts for user %s: %s", user.id, e)


async def run_adjustments_job():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                agent = WorkoutAdjustmentAgent(db)
                adjustments = await agent.run_daily_adjustments(user)

                if adjustments:
                    logger.info(
                        "Made %d adjustments for user %s", len(adjustments), user.id
                    )
                    for adj in adjustments:
                        logger.info("  - %s", adj["message"])
            except Exception as e:
                logger.exception(
                    "Failed to run adjustments for user %s: %s", user.id, e
                )


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
                logger.info("  - Synced: %s new workouts", result["synced"])
                logger.info(
                    "  - Matched: %s completed workouts to plan", result["matched"]
                )
                logger.info("  - Adjustments: %s plan changes", result["adjustments"])

                for adj in result.get("details", []):
                    logger.info("    - %s: %s", adj["type"], adj["message"])
            except Exception as e:
                logger.exception(
                    "Failed performance check for user %s: %s", user.id, e
                )


async def prune_raw_payloads_job():
    """Reduce storage costs by trimming old raw payload fields."""
    cutoff = datetime.utcnow() - timedelta(days=settings.raw_payload_retention_days)
    async with AsyncSessionLocal() as db:
        # Keep canonical metrics while removing large source payload blobs.
        await db.execute(
            update(CompletedWorkout)
            .where(
                CompletedWorkout.created_at < cutoff,
                CompletedWorkout.raw_data.isnot(None),
            )
            .values(raw_data=None)
        )

        # Webhook events are replay/debug artifacts; remove old records.
        await db.execute(
            delete(ProviderWebhookEvent).where(
                ProviderWebhookEvent.received_at < cutoff,
            )
        )
        await db.commit()
        logger.info(
            "Raw payload cleanup complete (retention_days=%s)",
            settings.raw_payload_retention_days,
        )


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

    scheduler.add_job(
        prune_raw_payloads_job,
        CronTrigger(hour=3, minute=15),
        id="prune_raw_payloads",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler():
    scheduler.shutdown()
