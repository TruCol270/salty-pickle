import json
import warnings
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_allowed_origins_to_list(raw: str) -> list[str]:
    """ALLOWED_ORIGINS may be a comma-separated list or a JSON array string (Railway-friendly)."""
    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    s = (raw or "").strip()
    if not s:
        return default_origins
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list):
                out = [str(x).strip() for x in data if str(x).strip()]
                return out or default_origins
        except json.JSONDecodeError:
            pass
    parts = [x.strip() for x in s.split(",") if x.strip()]
    return parts or default_origins


def _is_local_netloc(netloc: str) -> bool:
    host = netloc.split(":", 1)[0].lower()
    return host in {"localhost", "127.0.0.1"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/salty_pickle"
    redis_url: str = "redis://localhost:6379/0"

    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8080/auth/strava/callback"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8080/auth/google/callback"

    openai_api_key: str = ""

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    debug: bool = False
    app_public_url: str = "http://localhost:5173"
    api_public_url: str = "http://localhost:8080"
    # Must stay a plain str so EnvSettingsSource does not require JSON for list fields.
    # Use comma-separated URLs or a JSON array string; see parse_allowed_origins_to_list.
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )
    frontend_base_url: str = "http://localhost:5173"

    @field_validator("allowed_origins", mode="after")
    @classmethod
    def normalize_allowed_origins(cls, v: str) -> str:
        """Store JSON-array env values as comma-separated for a single predictable format."""
        s = v.strip()
        if not s:
            return "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
        if s.startswith("["):
            try:
                data = json.loads(s)
                if isinstance(data, list):
                    joined = ",".join(str(x).strip() for x in data if str(x).strip())
                    return (
                        joined
                        or "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
                    )
            except json.JSONDecodeError:
                pass
        return s

    @field_validator("raw_payload_retention_days", mode="after")
    @classmethod
    def validate_raw_payload_retention_days(cls, v: int) -> int:
        if v < 1:
            raise ValueError("RAW_PAYLOAD_RETENTION_DAYS must be at least 1")
        return v

    enable_scheduler: bool = False
    # Set automatically by worker_main.py before imports; also overridable via WORKER_SERVICE=1 in Railway.
    worker_service: bool = False

    # If set, POST /auth/token/bootstrap with header X-Bootstrap-Key can mint a JWT (dev/ops only).
    auth_bootstrap_key: str = ""

    gcp_project_id: str = ""
    gcp_region: str = ""

    whoop_client_id: str = ""
    whoop_client_secret: str = ""
    whoop_redirect_uri: str = "http://localhost:8080/auth/whoop/callback"

    raw_payload_retention_days: int = 90


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.debug and s.secret_key == "change-me-in-production":
        raise RuntimeError(
            "SECRET_KEY still has its default value. "
            "Set a strong random SECRET_KEY before running in production."
        )
    if s.debug and s.secret_key == "change-me-in-production":
        warnings.warn("Using default SECRET_KEY — not safe for production", stacklevel=2)
    # OAuth redirect allowlists only matter for the web API. Scheduler worker does not serve /auth.
    _skip_public_origin_check = s.worker_service or s.enable_scheduler
    if not s.debug and not _skip_public_origin_check:
        frontend_netloc = urlparse(s.frontend_base_url).netloc
        if _is_local_netloc(frontend_netloc):
            raise RuntimeError(
                "FRONTEND_BASE_URL points to localhost/127.0.0.1 in non-debug mode. "
                "Set FRONTEND_BASE_URL to your public frontend origin."
            )
        local_origins = []
        for origin in parse_allowed_origins_to_list(s.allowed_origins):
            netloc = urlparse(origin).netloc
            if _is_local_netloc(netloc):
                local_origins.append(origin)
        if local_origins:
            raise RuntimeError(
                "ALLOWED_ORIGINS contains localhost/127.0.0.1 in non-debug mode. "
                "Set ALLOWED_ORIGINS to public origins only."
            )
    return s
