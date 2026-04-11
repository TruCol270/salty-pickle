from datetime import datetime, timedelta
import secrets
import base64

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, OAuthState
from app.services.strava import StravaService
from app.services.whoop import WhoopService
from app.config import get_settings

settings = get_settings()
router = APIRouter()

OAUTH_STATE_TTL_MINUTES = 15


def generate_state() -> str:
    random_bytes = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(random_bytes).decode()


@router.get("/strava/authorize")
async def strava_authorize(
    redirect_url: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    state = generate_state()

    oauth_state = OAuthState(
        state=state,
        provider="strava",
        redirect_url=redirect_url,
        expires_at=datetime.utcnow() + timedelta(minutes=OAUTH_STATE_TTL_MINUTES),
    )
    db.add(oauth_state)
    await db.commit()

    service = StravaService(db)
    auth_url = service.get_authorization_url(
        state=state,
        redirect_uri=settings.strava_redirect_uri,
    )

    html = f"""<!DOCTYPE html>
<html>
<head><title>Strava Authorization</title></head>
<body>
<h1>Connect Strava</h1>
<p>Click the link below to authorize:</p>
<p><a href="{auth_url}">Authorize with Strava</a></p>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/strava/callback")
async def strava_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if not oauth_state or oauth_state.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    service = StravaService(db)
    tokens = await service.exchange_code_for_token(code)
    athlete = await service.get_athlete(tokens["access_token"])

    result = await db.execute(
        select(User).where(User.strava_athlete_id == str(athlete["id"]))
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=athlete.get("email"),
            strava_athlete_id=str(athlete["id"]),
        )
        db.add(user)

    user.strava_access_token = tokens["access_token"]
    user.strava_refresh_token = tokens["refresh_token"]
    user.strava_token_expires_at = datetime.fromtimestamp(tokens["expires_at"])

    await db.commit()

    await db.delete(oauth_state)
    await db.commit()


@router.get("/google/authorize")
async def google_authorize(
    redirect_url: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    from app.services.google_calendar import GoogleCalendarService

    state = generate_state()

    oauth_state = OAuthState(
        state=state,
        provider="google",
        redirect_url=redirect_url,
        expires_at=datetime.utcnow() + timedelta(minutes=OAUTH_STATE_TTL_MINUTES),
    )
    db.add(oauth_state)
    await db.commit()

    service = GoogleCalendarService(db)
    auth_url = service.get_authorization_url(
        state=state,
        redirect_uri=settings.google_redirect_uri,
    )

    html = f"""<!DOCTYPE html>
<html>
<head><title>Google Authorization</title></head>
<body>
<h1>Connect Google Calendar</h1>
<p>Click the link below to authorize:</p>
<p><a href="{auth_url}">Authorize with Google</a></p>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    from app.services.google_calendar import GoogleCalendarService

    result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if not oauth_state or oauth_state.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    service = GoogleCalendarService(db)
    tokens = await service.exchange_code_for_token(
        code,
        settings.google_redirect_uri,
    )

    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    user.google_access_token = tokens["access_token"]
    user.google_refresh_token = tokens["refresh_token"]

    await db.commit()

    await db.delete(oauth_state)
    await db.commit()

    return {"user_id": user.id, "message": "Google Calendar connected successfully"}


@router.get("/whoop/authorize")
async def whoop_authorize(
    db: AsyncSession = Depends(get_db),
):
    state = generate_state()

    oauth_state = OAuthState(
        state=state,
        provider="whoop",
        expires_at=datetime.utcnow() + timedelta(minutes=OAUTH_STATE_TTL_MINUTES),
    )
    db.add(oauth_state)
    await db.commit()

    service = WhoopService(db)
    auth_url = service.get_authorization_url(state=state)

    html = f"""<!DOCTYPE html>
<html>
<head><title>Whoop Authorization</title></head>
<body>
<h1>Connect Whoop</h1>
<p>Click the link below to authorize:</p>
<p><a href="{auth_url}">Authorize with Whoop</a></p>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/whoop/callback")
async def whoop_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if not oauth_state or oauth_state.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    service = WhoopService(db)
    tokens = await service.exchange_code_for_token(code)

    result = await db.execute(select(User))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="No user found")

    user.whoop_access_token = tokens.get("access_token")
    user.whoop_refresh_token = tokens.get("refresh_token")

    await db.commit()

    await db.delete(oauth_state)
    await db.commit()

    return {"user_id": user.id, "message": "Whoop connected successfully"}
