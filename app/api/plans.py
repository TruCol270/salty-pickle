from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.limiter import limiter
from app.models import User, TrainingPlan, PlannedWorkout
from app.schemas.plan import (
    TrainingPlanCreate,
    TrainingPlanUpdate,
    TrainingPlanResponse,
    PlanAdjustmentRequest,
    PlanAdjustmentResponse,
    AIGenerateRequest,
    AIGenerateResponse,
)
from app.services.plan_engine import PlanEngineService
from app.agents.adjustment_agent import WorkoutAdjustmentAgent
from app.agents.plan_generator import PlanGeneratorAgent
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("", response_model=list[TrainingPlanResponse])
async def list_plans(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(TrainingPlan).where(
        TrainingPlan.user_id == user.id
    ).order_by(desc(TrainingPlan.created_at))

    if status:
        query = query.where(TrainingPlan.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=TrainingPlanResponse)
async def create_plan(
    plan_data: TrainingPlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = PlanEngineService(db)
    plan = await service.create_plan(
        user_id=user.id,
        name=plan_data.name,
        start_date=plan_data.start_date,
        end_date=plan_data.end_date,
        workouts=[w.model_dump() for w in plan_data.workouts],
        goal_race_name=plan_data.goal_race_name,
        goal_race_date=plan_data.goal_race_date,
        goal_distance_km=plan_data.goal_distance_km,
    )

    return plan


@router.get("/active", response_model=TrainingPlanResponse)
async def get_active_plan(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = PlanEngineService(db)
    plan = await service.get_active_plan(user.id)

    if not plan:
        raise HTTPException(status_code=404, detail="No active plan found")

    return plan


@router.get("/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TrainingPlan).where(
            TrainingPlan.id == plan_id,
            TrainingPlan.user_id == user.id,
        )
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return plan


@router.put("/{plan_id}", response_model=TrainingPlanResponse)
async def update_plan(
    plan_id: int,
    updates: TrainingPlanUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TrainingPlan).where(
            TrainingPlan.id == plan_id,
            TrainingPlan.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Plan not found")

    service = PlanEngineService(db)
    plan = await service.update_plan(plan_id, **updates.model_dump(exclude_none=True))
    return plan


@router.post("/{plan_id}/adjust", response_model=PlanAdjustmentResponse)
async def trigger_adjustment(
    plan_id: int,
    adjustment_data: PlanAdjustmentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = WorkoutAdjustmentAgent(db)

    if adjustment_data.trigger == "missed":
        result = await db.execute(
            select(PlannedWorkout)
            .join(TrainingPlan)
            .options(selectinload(PlannedWorkout.plan))
            .where(
                PlannedWorkout.id == adjustment_data.workout_id,
                TrainingPlan.id == plan_id,
                TrainingPlan.user_id == user.id,
            )
        )
        workout = result.scalar_one_or_none()

        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

        adjustment = await agent.adjust_for_missed_workout(user, workout)

    elif adjustment_data.trigger == "low_recovery":
        result = await db.execute(
            select(PlannedWorkout)
            .join(TrainingPlan)
            .options(selectinload(PlannedWorkout.plan))
            .where(
                PlannedWorkout.id == adjustment_data.workout_id,
                TrainingPlan.id == plan_id,
                TrainingPlan.user_id == user.id,
            )
        )
        workout = result.scalar_one_or_none()

        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

        adjustment = await agent.adjust_for_low_recovery(user, workout)

    else:
        raise HTTPException(status_code=400, detail="Unknown trigger type")

    if not adjustment:
        raise HTTPException(status_code=400, detail="No adjustment needed")

    return PlanAdjustmentResponse(
        adjustment_id=adjustment["adjustment_id"],
        adjustment_type=adjustment["adjustment_type"],
        new_workouts=[],
        message=adjustment["message"],
    )


@router.post("/ai-generate", response_model=AIGenerateResponse)
@limiter.limit("5/minute")
async def generate_plan_with_ai(
    request: Request,
    ai_request: AIGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.strava_access_token:
        raise HTTPException(
            status_code=400,
            detail="Please connect Strava first to generate a personalized plan",
        )
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI plan generation is not configured. Set OPENAI_API_KEY before private beta launch.",
        )

    agent = PlanGeneratorAgent(db)

    try:
        result = await agent.generate_training_plan(
            user=user,
            race_name=ai_request.race_name,
            race_date=ai_request.race_date,
            race_distance_km=ai_request.race_distance_km,
            current_fitness_level=ai_request.current_fitness_level,
            weekly_mileage_km=ai_request.weekly_mileage_km,
            years_experience=ai_request.years_experience,
            preferred_days=ai_request.preferred_days,
            preferred_time=ai_request.preferred_time,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
