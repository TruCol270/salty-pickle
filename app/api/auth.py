import logging
from datetime import datetime, timedelta
import secrets
import base64
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user
from app.limiter import limiter
from app.models import User, OAuthState
from app.schemas.auth import TokenResponse
from app.security import create_access_token, decode_access_token
from app.services.strava import StravaService
from app.services.whoop import WhoopService
from app.config import get_settings, parse_allowed_origins_to_list

logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter()


def _provider_authorize_response(
    auth_url: str,
    title: str,
    heading: str,
    auto_redirect: bool,
):
    """Return direct redirect by default; keep HTML fallback for manual/dev flows."""
    if auto_redirect:
        return RedirectResponse(url=auth_url, status_code=302)
    html = f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
<h1>{heading}</h1>
<p>Click the link below to authorize:</p>
<p><a href="{auth_url}">Authorize</a></p>
</body>
</html>"""
    return HTMLResponse(content=html)


def _normalized_origin(s: str) -> str | None:
    parsed = urlparse(s)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
    return None


def _oauth_redirect_origin_allowlist() -> frozenset[str]:
    """Origins (scheme+host+port) allowed for post-OAuth redirects."""
    origins: set[str] = set()
    for origin in parse_allowed_origins_to_list(settings.allowed_origins):
        normalized = _normalized_origin(origin)
        if normalized:
            origins.add(normalized)
    normalized_frontend = _normalized_origin(settings.frontend_base_url)
    if normalized_frontend:
        origins.add(normalized_frontend)
    return frozenset(origins)


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
    provided_origin = _normalized_origin(url)
    allowed = _oauth_redirect_origin_allowlist()
    if not provided_origin or provided_origin not in allowed:
        logger.warning(
            "Rejected OAuth redirect_url origin",
            extra={
                "provided_origin": provided_origin,
                "allowed_origin_count": len(allowed),
            },
        )
        raise HTTPException(
            status_code=400,
            detail="redirect_url origin is not allowed",
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
        normalized_origin = _normalized_origin(url)
        if not normalized_origin or normalized_origin not in _oauth_redirect_origin_allowlist():
            raise ValueError("origin not allowed")
        return url
    except ValueError:
        logger.warning("Ignored disallowed OAuth redirect_url from stored state; using default")
        return default


def _redirect_with_session_token(redirect_url: str | None, user_id: int) -> RedirectResponse:
    base = safe_oauth_redirect_for_callback(redirect_url)
    token = create_access_token(user_id)
    joiner = "&" if "#" in base else "#"
    url = f"{base}{joiner}access_token={token}&user_id={user_id}"
    return RedirectResponse(url=url, status_code=302)


def generate_state() -> str:
    random_bytes = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(random_bytes).decode()


class OAuthAuthorizeUrlRequest(BaseModel):
    redirect_url: str | None = None


def _create_oauth_state(
    *,
    db: AsyncSession,
    provider: str,
    state: str,
    redirect_url: str | None,
    user_id: int | None,
) -> OAuthState:
    oauth_state = OAuthState(
        state=state,
        provider=provider,
        redirect_url=redirect_url,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(oauth_state)
    return oauth_state


def _resolve_user_id_from_auth(authorization: str | None) -> int:
    token: str | None = None
    if authorization:
        auth_value = authorization.strip()
        if auth_value.lower().startswith("bearer "):
            token = auth_value[7:].strip() or None
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from e


@router.get("/strava/authorize")
async def strava_authorize(
    redirect_url: str = Query(default=None),
    user_id: int = Query(default=None, description="Authenticated user ID (omit for new sign-ups)"),
    auto_redirect: bool = Query(
        default=True,
        description="When true (default), immediately redirect to provider OAuth page.",
    ),
    db: AsyncSession = Depends(get_db),
):
    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(redirect_url)

    _create_oauth_state(
        db=db,
        provider="strava",
        state=state,
        redirect_url=validated_redirect,
        user_id=user_id,
    )
    await db.commit()

    service = StravaService(db)
    auth_url = service.get_authorization_url(
        state=state,
        redirect_uri=settings.strava_redirect_uri,
    )

    return _provider_authorize_response(
        auth_url=auth_url,
        title="Strava Authorization",
        heading="Connect Strava",
        auto_redirect=auto_redirect,
    )


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
    authorization: str | None = Header(default=None),
    auto_redirect: bool = Query(
        default=True,
        description="When true (default), immediately redirect to provider OAuth page.",
    ),
    db: AsyncSession = Depends(get_db),
):
    from app.services.google_calendar import GoogleCalendarService

    user_id = _resolve_user_id_from_auth(authorization)
    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(redirect_url)

    _create_oauth_state(
        db=db,
        provider="google",
        state=state,
        redirect_url=validated_redirect,
        user_id=user_id,
    )
    await db.commit()

    service = GoogleCalendarService(db)
    auth_url = service.get_authorization_url(
        state=state,
        redirect_uri=settings.google_redirect_uri,
    )

    return _provider_authorize_response(
        auth_url=auth_url,
        title="Google Authorization",
        heading="Connect Google Calendar",
        auto_redirect=auto_redirect,
    )


@router.post("/google/authorize-url")
async def google_authorize_url(
    payload: OAuthAuthorizeUrlRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.google_calendar import GoogleCalendarService

    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(payload.redirect_url)
    _create_oauth_state(
        db=db,
        provider="google",
        state=state,
        redirect_url=validated_redirect,
        user_id=user.id,
    )
    await db.commit()

    service = GoogleCalendarService(db)
    auth_url = service.get_authorization_url(
        state=state,
        redirect_uri=settings.google_redirect_uri,
    )
    return {"auth_url": auth_url}


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
    authorization: str | None = Header(default=None),
    auto_redirect: bool = Query(
        default=True,
        description="When true (default), immediately redirect to provider OAuth page.",
    ),
    db: AsyncSession = Depends(get_db),
):
    user_id = _resolve_user_id_from_auth(authorization)
    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(redirect_url)

    _create_oauth_state(
        db=db,
        provider="whoop",
        state=state,
        redirect_url=validated_redirect,
        user_id=user_id,
    )
    await db.commit()

    service = WhoopService(db)
    auth_url = service.get_authorization_url(state=state)

    return _provider_authorize_response(
        auth_url=auth_url,
        title="Whoop Authorization",
        heading="Connect Whoop",
        auto_redirect=auto_redirect,
    )


@router.post("/whoop/authorize-url")
async def whoop_authorize_url(
    payload: OAuthAuthorizeUrlRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    state = generate_state()
    validated_redirect = validate_oauth_redirect_url_param(payload.redirect_url)
    _create_oauth_state(
        db=db,
        provider="whoop",
        state=state,
        redirect_url=validated_redirect,
        user_id=user.id,
    )
    await db.commit()

    service = WhoopService(db)
    auth_url = service.get_authorization_url(state=state)
    return {"auth_url": auth_url}


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


@router.get("/provider-callbacks")
async def provider_callbacks():
    """Operational visibility for OAuth callback and frontend redirect config."""
    return {
        "frontend_base_url": settings.frontend_base_url,
        "allowed_origins": parse_allowed_origins_to_list(settings.allowed_origins),
        "providers": {
            "strava": settings.strava_redirect_uri,
            "google": settings.google_redirect_uri,
            "whoop": settings.whoop_redirect_uri,
        },
    }


@router.post("/token/bootstrap", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth)
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
