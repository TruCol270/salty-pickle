from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/salty_pickle"
    redis_url: str = "redis://localhost:6379/0"

    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8000/auth/strava/callback"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    openai_api_key: str = ""

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000"]

    gcp_project_id: str = ""
    gcp_region: str = "us-central1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
