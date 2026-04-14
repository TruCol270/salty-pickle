import json
import warnings
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_allowed_origins_to_list(raw: str) -> list[str]:
    """ALLOWED_ORIGINS may be a comma-separated list or a JSON array string (Railway-friendly)."""
    s = (raw or "").strip()
    if not s:
        return ["http://localhost:3000"]
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list):
                out = [str(x).strip() for x in data if str(x).strip()]
                return out or ["http://localhost:3000"]
        except json.JSONDecodeError:
            pass
    parts = [x.strip() for x in s.split(",") if x.strip()]
    return parts or ["http://localhost:3000"]


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
    # Must stay a plain str so EnvSettingsSource does not require JSON for list fields.
    # Use comma-separated URLs or a JSON array string; see parse_allowed_origins_to_list.
    allowed_origins: str = Field(default="http://localhost:3000")
    frontend_base_url: str = "http://localhost:3000"

    @field_validator("allowed_origins", mode="after")
    @classmethod
    def normalize_allowed_origins(cls, v: str) -> str:
        """Store JSON-array env values as comma-separated for a single predictable format."""
        s = v.strip()
        if not s:
            return "http://localhost:3000"
        if s.startswith("["):
            try:
                data = json.loads(s)
                if isinstance(data, list):
                    joined = ",".join(str(x).strip() for x in data if str(x).strip())
                    return joined or "http://localhost:3000"
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
    return s
