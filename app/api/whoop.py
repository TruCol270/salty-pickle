import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user
from app.models import User, ProviderWebhookEvent, WhoopRecoverySample, SyncRunStatus
from app.services.whoop import WhoopService
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/recovery")
async def get_recovery_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get latest Whoop recovery data."""
    if not user.whoop_access_token:
        return {
            "connected": False,
            "message": "Connect Whoop to get recovery data",
        }

    service = WhoopService(db)
    recovery = await service.get_latest_recovery(user)

    if not recovery:
        return {"connected": True, "recovery": None}

    recommendation = await service.get_recovery_recommendation(recovery)

    return {
        "connected": True,
        "recovery": recovery,
        "recommendation": recommendation,
    }


@router.get("/recovery/trend")
async def get_recovery_trend(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Recovery / HRV / RHR points for charts (last N days)."""
    if not user.whoop_access_token:
        return {"connected": False, "points": []}

    service = WhoopService(db)
    points = await service.get_recovery_history(user, days=min(days, 30))
    return {"connected": True, "points": points}


@router.post("/webhook/register")
async def register_webhook(
    db: AsyncSession = Depends(get_db),
):
    """Register a webhook subscription with Whoop."""
    if not settings.whoop_client_id:
        raise HTTPException(status_code=400, detail="Whoop credentials not configured")

    callback_url = f"{settings.whoop_redirect_uri.replace('/auth/whoop/callback', '')}/api/v1/whoop/webhook"

    service = WhoopService(db)
    try:
        result = await service.register_webhook(callback_url)
        return {"registered": True, "webhook": result}
    except Exception as e:
        logger.exception("Failed to register Whoop webhook: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to register webhook with provider",
        )


@router.post("/webhook")
async def whoop_webhook(
    request: Request,
    x_whoop_signature: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Receive real-time Whoop events (recovery, sleep, workout)."""
    payload_bytes = await request.body()

    if not settings.whoop_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Webhook signature secret is not configured",
        )

    # Verify signature if secret is configured
    if not x_whoop_signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    service = WhoopService(db)
    if not service.verify_webhook_signature(payload_bytes, x_whoop_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = payload.get("event_type", "")
    whoop_user_id = str(payload.get("user_id", ""))
    event_id = str(payload.get("id", "")) or None

    if event_id:
        dedupe = await db.execute(
            select(ProviderWebhookEvent).where(
                ProviderWebhookEvent.provider == "whoop",
                ProviderWebhookEvent.event_id == event_id,
            )
        )
        existing = dedupe.scalar_one_or_none()
        if existing and existing.status == SyncRunStatus.SUCCESS:
            return {"status": "duplicate"}

    webhook_event = ProviderWebhookEvent(
        provider="whoop",
        event_type=event_type,
        provider_user_id=whoop_user_id or None,
        event_id=event_id,
        status=SyncRunStatus.STARTED,
        payload=payload,
    )
    db.add(webhook_event)
    await db.flush()

    logger.info("Whoop webhook received: %s for user %s", event_type, whoop_user_id)

    result = await db.execute(select(User).where(User.whoop_user_id == whoop_user_id))
    user = result.scalars().first()

    if not user:
        logger.warning("Whoop webhook for unknown whoop_user_id=%s", whoop_user_id)
        webhook_event.status = SyncRunStatus.FAILED
        webhook_event.error_message = "No user mapped to whoop_user_id"
        webhook_event.processed_at = datetime.utcnow()
        await db.commit()
        return {"status": "no_user"}

    webhook_event.user_id = user.id

    try:
        if event_type == "recovery.updated":
            await _handle_recovery_event(payload, user, db)
        elif event_type == "sleep.updated":
            await _handle_sleep_event(payload, user, db)
        elif event_type == "workout.updated":
            await _handle_workout_event(payload, user, db)

        webhook_event.status = SyncRunStatus.SUCCESS
        webhook_event.processed_at = datetime.utcnow()
        await db.commit()
        return {"status": "ok"}
    except Exception as exc:
        await db.rollback()
        webhook_event.status = SyncRunStatus.FAILED
        webhook_event.error_message = str(exc)
        webhook_event.processed_at = datetime.utcnow()
        db.add(webhook_event)
        await db.commit()
        raise


async def _handle_recovery_event(payload: dict, user: User, db: AsyncSession):
    """Process a recovery.updated event and adjust training plan."""
    from app.services.performance_analyzer import PerformanceAnalyzer

    service = WhoopService(db)
    recovery_data = service.parse_recovery_event(payload)

    if not recovery_data:
        return

    sample = WhoopRecoverySample(
        user_id=user.id,
        whoop_user_id=str(payload.get("user_id", "")) or user.whoop_user_id,
        source="webhook",
        source_id=str(payload.get("id", "")) or None,
        cycle_id=str(recovery_data.get("cycle_id", "")) or None,
        recovery_score=int((recovery_data.get("recovery_score", 0) or 0) * 100),
        resting_heart_rate=recovery_data.get("resting_heart_rate"),
        hrv_rmssd_milli=recovery_data.get("hrv_rmssd_milli"),
        spo2_percentage=recovery_data.get("spo2_percentage"),
        skin_temp_celsius=recovery_data.get("skin_temp_celsius"),
        recorded_at=datetime.fromisoformat(
            recovery_data["cycle_date"].replace("Z", "+00:00")
        ).replace(tzinfo=None)
        if recovery_data.get("cycle_date")
        else None,
        payload=payload,
    )
    db.add(sample)

    # Store whoop_user_id if not set
    if not user.whoop_user_id and recovery_data.get("user_id"):
        user.whoop_user_id = str(recovery_data["user_id"])
        await db.flush()

    recommendation = await service.get_recovery_recommendation(recovery_data)
    recovery_score = recovery_data.get("recovery_score", 0.5)

    logger.info(
        "Recovery score: %.0f%%, recommendation: %s",
        (recovery_score * 100) if recovery_score <= 1 else recovery_score,
        recommendation,
    )

    # Only adjust plan for low recovery - don't spam adjustments
    if recommendation in ("easy", "rest"):
        from app.models import TrainingPlan, PlannedWorkout, PlanStatus
        from sqlalchemy import and_

        result = await db.execute(
            select(TrainingPlan).where(
                and_(
                    TrainingPlan.user_id == user.id,
                    TrainingPlan.status == PlanStatus.ACTIVE,
                )
            )
        )
        plan = result.scalars().first()

        if not plan:
            return

        today = datetime.utcnow().date()
        result = await db.execute(
            select(PlannedWorkout)
            .where(
                and_(
                    PlannedWorkout.plan_id == plan.id,
                    PlannedWorkout.completed == False,  # noqa: E712
                )
            )
            .order_by(PlannedWorkout.scheduled_date)
        )
        upcoming = result.scalars().all()

        # Find today's or tomorrow's workout
        target = None
        for w in upcoming:
            if w.scheduled_date and w.scheduled_date.date() >= today:
                target = w
                break

        if not target:
            return

        if recommendation == "rest":
            target.notes = (
                (target.notes or "")
                + f"\n[Auto-adjusted: Rest day recommended (Whoop recovery {recovery_score:.0%})]"
            )
            target.target_distance_km = 0 if target.target_distance_km else None
            target.workout_type = "rest"
        elif recommendation == "easy":
            if target.workout_type in ("tempo_run", "interval_run", "long_run"):
                target.notes = (
                    (target.notes or "")
                    + f"\n[Auto-adjusted: Easy run instead (Whoop recovery {recovery_score:.0%})]"
                )
                target.workout_type = "easy_run"
                if target.target_distance_km:
                    target.target_distance_km = round(
                        target.target_distance_km * 0.7, 1
                    )

        await db.flush()
        logger.info(
            "Adjusted workout %s to %s based on Whoop recovery",
            target.id,
            target.workout_type,
        )


async def _handle_sleep_event(payload: dict, user: User, db: AsyncSession):
    """Log sleep data — used for future recovery modeling."""
    data = payload.get("data", {})
    score = data.get("score", {})
    sleep_efficiency = score.get("sleep_efficiency_percentage", 0)
    sleep_hours = (data.get("end") or 0) - (data.get("start") or 0)

    logger.info(
        "Sleep event for user %s: %.0f%% efficiency", user.id, sleep_efficiency
    )


async def _handle_workout_event(payload: dict, user: User, db: AsyncSession):
    """Trigger a Strava sync when Whoop sees a workout."""
    from app.services.workout_sync import WorkoutSyncService
    from datetime import timedelta

    logger.info("Workout event for user %s, triggering Strava sync", user.id)

    if user.strava_access_token:
        try:
            sync_service = WorkoutSyncService(db)
            synced = await sync_service.sync_from_strava(
                user,
                after=datetime.utcnow() - timedelta(hours=6),
            )
            logger.info(
                "Synced %d workouts after Whoop workout event", len(synced)
            )
        except Exception as e:
            logger.exception("Failed Strava sync after Whoop workout event: %s", e)
