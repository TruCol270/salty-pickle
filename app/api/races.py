from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.race_analyzer import RaceAnalyzer

router = APIRouter()


@router.post("/analyze")
async def analyze_race_url(
    url: str,
    race_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Analyze a race URL to extract course information."""
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    analyzer = RaceAnalyzer()

    try:
        race_info = await analyzer.analyze_url(url)

        if race_date and not race_info.get("race_date"):
            try:
                race_info["race_date"] = datetime.fromisoformat(
                    race_date.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        advice = analyzer.get_training_advice(race_info)

        return {
            "race_info": race_info,
            "training_advice": advice,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze race: {str(e)}")
