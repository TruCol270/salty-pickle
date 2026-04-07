from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.services.whoop import WhoopService
from app.config import get_settings

settings = get_settings()
router = APIRouter()


@router.get("/recovery")
async def get_recovery_data(
    db: AsyncSession = Depends(get_db),
):
    """Get latest Whoop recovery data."""
    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
        raise HTTPException(
            status_code=500, detail=f"Failed to register webhook: {str(e)}"
        )


@router.post("/webhook")
async def whoop_webhook(
    request: Request,
    x_whoop_signature: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Receive real-time Whoop events (recovery, sleep, workout)."""
    payload_bytes = await request.body()

    # Verify signature if secret is configured
    if settings.whoop_client_secret and x_whoop_signature:
        service = WhoopService(db)
        if not service.verify_webhook_signature(payload_bytes, x_whoop_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = payload.get("event_type", "")
    whoop_user_id = str(payload.get("user_id", ""))

    print(f"Whoop webhook received: {event_type} for user {whoop_user_id}")

    # Find user by whoop_user_id
    result = await db.execute(select(User).where(User.whoop_user_id == whoop_user_id))
    user = result.scalars().first()

    # Fall back to first user if whoop_user_id not set yet
    if not user:
        result = await db.execute(select(User))
        user = result.scalars().first()

    if not user:
        return {"status": "no_user"}

    if event_type == "recovery.updated":
        await _handle_recovery_event(payload, user, db)
    elif event_type == "sleep.updated":
        await _handle_sleep_event(payload, user, db)
    elif event_type == "workout.updated":
        await _handle_workout_event(payload, user, db)

    return {"status": "ok"}


async def _handle_recovery_event(payload: dict, user: User, db: AsyncSession):
    """Process a recovery.updated event and adjust training plan."""
    from app.services.performance_analyzer import PerformanceAnalyzer

    service = WhoopService(db)
    recovery_data = service.parse_recovery_event(payload)

    if not recovery_data:
        return

    # Store whoop_user_id if not set
    if not user.whoop_user_id and recovery_data.get("user_id"):
        user.whoop_user_id = str(recovery_data["user_id"])
        await db.commit()

    recommendation = await service.get_recovery_recommendation(recovery_data)
    recovery_score = recovery_data.get("recovery_score", 0.5)

    print(f"Recovery score: {recovery_score:.0%}, recommendation: {recommendation}")

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
                    PlannedWorkout.completed == "false",
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

        await db.commit()
        print(
            f"Adjusted workout {target.id} to {target.workout_type} based on Whoop recovery"
        )


async def _handle_sleep_event(payload: dict, user: User, db: AsyncSession):
    """Log sleep data — used for future recovery modeling."""
    data = payload.get("data", {})
    score = data.get("score", {})
    sleep_efficiency = score.get("sleep_efficiency_percentage", 0)
    sleep_hours = (data.get("end") or 0) - (data.get("start") or 0)

    print(f"Sleep event for user {user.id}: {sleep_efficiency:.0f}% efficiency")


async def _handle_workout_event(payload: dict, user: User, db: AsyncSession):
    """Trigger a Strava sync when Whoop sees a workout."""
    from app.services.workout_sync import WorkoutSyncService
    from datetime import timedelta

    print(f"Workout event for user {user.id}, triggering Strava sync")

    if user.strava_access_token:
        try:
            sync_service = WorkoutSyncService(db)
            synced = await sync_service.sync_from_strava(
                user,
                after=datetime.utcnow() - timedelta(hours=6),
            )
            print(f"Synced {len(synced)} workouts after Whoop workout event")
        except Exception as e:
            print(f"Failed Strava sync after Whoop workout event: {e}")
