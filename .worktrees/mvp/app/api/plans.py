from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import User, TrainingPlan, PlanStatus, PlannedWorkout
from app.schemas.plan import (
    TrainingPlanCreate,
    TrainingPlanUpdate,
    TrainingPlanResponse,
    PlanAdjustmentRequest,
    PlanAdjustmentResponse,
    AIGenerateRequest,
    AIGenerateResponse,
)
from app.cache import cache_get, cache_set, cache_delete
from app.services.plan_engine import PlanEngineService
from app.agents.adjustment_agent import WorkoutAdjustmentAgent
from app.agents.plan_generator import PlanGeneratorAgent

router = APIRouter()


@router.get("", response_model=list[TrainingPlanResponse])
async def list_plans(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(TrainingPlan).order_by(desc(TrainingPlan.created_at))

    if status:
        query = query.where(TrainingPlan.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=TrainingPlanResponse)
async def create_plan(
    plan_data: TrainingPlanCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    user = result.scalars().first()

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
):
    cached = await cache_get("active_plan")
    if cached is not None:
        return cached

    result = await db.execute(select(User))
    user = result.scalars().first()

    service = PlanEngineService(db)
    plan = await service.get_active_plan(user.id)

    if not plan:
        raise HTTPException(status_code=404, detail="No active plan found")

    response = TrainingPlanResponse.model_validate(plan, from_attributes=True)
    await cache_set("active_plan", response.model_dump(), ttl=120)

    return plan


@router.get("/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TrainingPlan).where(TrainingPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return plan


@router.put("/{plan_id}", response_model=TrainingPlanResponse)
async def update_plan(
    plan_id: int,
    updates: TrainingPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = PlanEngineService(db)
    plan = await service.update_plan(plan_id, **updates.model_dump(exclude_none=True))
    return plan


@router.post("/{plan_id}/adjust", response_model=PlanAdjustmentResponse)
async def trigger_adjustment(
    plan_id: int,
    adjustment_data: PlanAdjustmentRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    user = result.scalars().first()

    agent = WorkoutAdjustmentAgent(db)

    if adjustment_data.trigger == "missed":
        result = await db.execute(
            select(PlannedWorkout).where(
                PlannedWorkout.id == adjustment_data.workout_id
            )
        )
        workout = result.scalar_one_or_none()

        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

        adjustment = await agent.adjust_for_missed_workout(user, workout)

    elif adjustment_data.trigger == "low_recovery":
        result = await db.execute(
            select(PlannedWorkout).where(
                PlannedWorkout.id == adjustment_data.workout_id
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
async def generate_plan_with_ai(
    request: AIGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.strava_access_token:
        raise HTTPException(
            status_code=400,
            detail="Please connect Strava first to generate a personalized plan",
        )

    agent = PlanGeneratorAgent(db)

    try:
        result = await agent.generate_training_plan(
            user=user,
            race_name=request.race_name,
            race_date=request.race_date,
            race_distance_km=request.race_distance_km,
            current_fitness_level=request.current_fitness_level,
            weekly_mileage_km=request.weekly_mileage_km,
            years_experience=request.years_experience,
            preferred_days=request.preferred_days,
            preferred_time=request.preferred_time,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
