from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.services.whoop import WhoopService

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
        return {
            "connected": True,
            "recovery": None,
        }

    recommendation = await service.get_recovery_recommendation(recovery)

    return {
        "connected": True,
        "recovery": recovery,
        "recommendation": recommendation,
    }
