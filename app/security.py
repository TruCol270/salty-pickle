"""JWT helpers for authenticated API access."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
    except JWTError as e:
        raise ValueError("invalid token") from e
    sub = payload.get("sub")
    if sub is None:
        raise ValueError("missing subject")
    return int(sub)
