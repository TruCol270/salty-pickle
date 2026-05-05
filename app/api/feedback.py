from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.limiter import limiter
from app.models import Feedback

settings = get_settings()
router = APIRouter()


class FeedbackRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    email: EmailStr | None = None
    page: str | None = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    ok: bool
    id: int


@router.post("/feedback", response_model=FeedbackResponse)
@limiter.limit(settings.rate_limit_feedback)
async def create_feedback(
    request: Request,
    payload: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    feedback = Feedback(
        message=payload.message,
        email=str(payload.email) if payload.email else None,
        page=payload.page,
        created_at=datetime.utcnow(),
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return FeedbackResponse(ok=True, id=feedback.id)
