from datetime import datetime, timedelta
from typing import Optional
import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User

settings = get_settings()


class StravaService:
    AUTH_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    API_URL = "https://www.strava.com/api/v3"

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": settings.strava_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "read,activity:read",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"

    async def exchange_code_for_token(self, code: str) -> dict:
        # Strava requires redirect_uri to match the one used in /oauth/authorize.
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": settings.strava_client_id,
                    "client_secret": settings.strava_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.strava_redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_athlete(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/athlete",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_activities(
        self,
        access_token: str,
        after: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 30,
    ) -> list[dict]:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"page": page, "per_page": per_page}

        if after:
            params["after"] = int(after.timestamp())

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/activities",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def refresh_token_if_needed(self, user: User) -> User:
        if not user.strava_token_expires_at:
            return user

        if user.strava_token_expires_at > datetime.utcnow() + timedelta(minutes=5):
            return user

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": settings.strava_client_id,
                    "client_secret": settings.strava_client_secret,
                    "refresh_token": user.strava_refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            tokens = response.json()

            user.strava_access_token = tokens["access_token"]
            user.strava_refresh_token = tokens["refresh_token"]
            user.strava_token_expires_at = datetime.fromtimestamp(tokens["expires_at"])
            self.db.add(user)
            await self.db.commit()

        return user
