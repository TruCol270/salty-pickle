import logging
from datetime import datetime, timedelta
import secrets
import base64
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.limiter import limiter
from app.models import User, OAuthState
from app.schemas.auth import TokenResponse
from app.security import create_access_token
from app.services.strava import StravaService
from app.services.whoop import WhoopService
from app.config import get_settings, parse_allowed_origins_to_list

logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter()


def _oauth_redirect_netloc_allowlist() -> frozenset[str]:
    """Netlocs (host:port) allowed for post-OAuth redirects (must match app origins)."""
    netlocs: set[str] = set()
    for origin in parse_allowed_origins_to_list(settings.allowed_origins):
        p = urlparse(origin)
        if p.scheme in ("http", "https") and p.netloc:
            netlocs.add(p.netloc.lower())
    p = urlparse(settings.frontend_base_url)
    if p.scheme in ("http", "https") and p.netloc:
        netlocs.add(p.netloc.lower())
    return frozenset(netlocs)


def validate_oauth_redirect_url_param(raw: str | None) -> str | None:
    """Validate user-supplied redirect_url for OAuth authorize. Returns normalized URL or None."""
    if raw is None or not str(raw).strip():
        return None
    url = str(raw).strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400, detail="redirect_url must use http or https"
        )
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="redirect_url must include a host")
    if parsed.username is not None or parsed.password is not None:
        raise HTTPException(status_code=400, detail="redirect_url must not include credentials")
    allowed = _oauth_redirect_netloc_allowlist()
    if parsed.netloc.lower() not in allowed:
        raise HTTPException(
            status_code=400,
            detail="redirect_url host is not allowed",
        )
    return url


def safe_oauth_redirect_for_callback(stored: str | None) -> str:
    """Resolve redirect target after OAuth; fall back to default if stored value is disallowed."""
    default = f"{settings.frontend_base_url.rstrip('/')}/integrations"
    if stored is None or not str(stored).strip():
        return default
    try:
        url = str(stored).strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("bad url")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("credentials in url")
        if parsed.netloc.lower() not in _oauth_redirect_netloc_allowlist():
            raise ValueError("host not allowed")
        return url
    except ValueError:
        logger.warning("Ignored disallowed OAuth redirect_url from stored state; using default")
        return default


def _redirect_with_session_token(redirect_url: str | None, user_id: int) -> RedirectResponse:
    base = safe_oauth_redirect_for_callback(redirect_url)
    token = create_access_token(user_id)
    joiner = "&" if "?" in base else "?"
    url = f"{base}{joiner}access_token={token}"
    return RedirectResponse(url=url, status_code=302)


def generate_state() -> str:
    random_bytes = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(random_bytes).decode()


@router.get("/strava/authorize")
async def strava_authorize(
    redirect_url: str = Query(default=None),
    user_id: int = Query(default=None, description="Authenticated user ID (omit for new sign-ups)"),
    db: AsyncSession = Depends(get_db),
):
    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(redirect_url)

    oauth_state = OAuthState(
        state=state,
        provider="strava",
        redirect_url=validated_redirect,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
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
        await db.flush()

    user.strava_access_token = tokens["access_token"]
    user.strava_refresh_token = tokens["refresh_token"]
    user.strava_token_expires_at = datetime.fromtimestamp(tokens["expires_at"])

    await db.commit()

    redirect_stored = oauth_state.redirect_url
    await db.delete(oauth_state)
    await db.commit()

    return _redirect_with_session_token(redirect_stored, user.id)


@router.get("/google/authorize")
async def google_authorize(
    redirect_url: str = Query(default=None),
    user_id: int = Query(..., description="Authenticated user ID initiating the OAuth flow"),
    db: AsyncSession = Depends(get_db),
):
    from app.services.google_calendar import GoogleCalendarService

    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(redirect_url)

    oauth_state = OAuthState(
        state=state,
        provider="google",
        redirect_url=validated_redirect,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
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

    if not oauth_state.user_id:
        raise HTTPException(status_code=400, detail="OAuth state missing user_id")

    result = await db.execute(select(User).where(User.id == oauth_state.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.google_access_token = tokens["access_token"]
    user.google_refresh_token = tokens["refresh_token"]

    await db.commit()

    redirect_stored = oauth_state.redirect_url
    await db.delete(oauth_state)
    await db.commit()

    return _redirect_with_session_token(redirect_stored, user.id)


@router.get("/whoop/authorize")
async def whoop_authorize(
    redirect_url: str = Query(default=None),
    user_id: int = Query(..., description="Authenticated user ID initiating the OAuth flow"),
    db: AsyncSession = Depends(get_db),
):
    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(redirect_url)

    oauth_state = OAuthState(
        state=state,
        provider="whoop",
        redirect_url=validated_redirect,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
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

    if not oauth_state.user_id:
        raise HTTPException(status_code=400, detail="OAuth state missing user_id")

    result = await db.execute(select(User).where(User.id == oauth_state.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.whoop_access_token = tokens.get("access_token")
    user.whoop_refresh_token = tokens.get("refresh_token")

    whoop_profile = tokens.get("user_id")
    if whoop_profile:
        user.whoop_user_id = str(whoop_profile)

    await db.commit()

    redirect_stored = oauth_state.redirect_url
    await db.delete(oauth_state)
    await db.commit()

    return _redirect_with_session_token(redirect_stored, user.id)


@router.post("/token/bootstrap", response_model=TokenResponse)
@limiter.limit("5/minute")
async def bootstrap_session_token(
    request: Request,
    x_bootstrap_key: str | None = Header(default=None, alias="X-Bootstrap-Key"),
    db: AsyncSession = Depends(get_db),
):
    """Mint a JWT for the first user; only when AUTH_BOOTSTRAP_KEY matches (dev/ops)."""
    if not settings.auth_bootstrap_key or x_bootstrap_key != settings.auth_bootstrap_key:
        raise HTTPException(status_code=403, detail="Bootstrap is not configured or key is invalid")
    result = await db.execute(select(User))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="No user in database")
    return TokenResponse(
        access_token=create_access_token(user.id),
        user_id=user.id,
    )
