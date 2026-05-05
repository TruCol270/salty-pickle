import os
from datetime import datetime
from typing import Optional

import httpx
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

settings = get_settings()


class GoogleCalendarService:
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
        )
        flow.oauth2session.redirect_uri = redirect_uri
        return flow.authorization_url(prompt="consent", state=state)[0]

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
        )
        flow.oauth2session.redirect_uri = redirect_uri
        flow.fetch_token(code=code)
        return {
            "access_token": flow.credentials.token,
            "refresh_token": flow.credentials.refresh_token,
        }

    async def create_event(
        self,
        user: User,
        summary: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        location: Optional[str] = None,
    ) -> dict:
        credentials = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )

        timezone = user.timezone if user.timezone else "America/New_York"

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": timezone,
            },
        }

        if location:
            event["location"] = location

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": f"Bearer {credentials.token}"},
                json=event,
            )
            if response.status_code != 200:
                print(f"Calendar API error: {response.status_code}")
                print(f"Response text: {response.text}")
            response.raise_for_status()
            return response.json()

    async def update_event(
        self,
        user: User,
        event_id: str,
        summary: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict:
        credentials = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": user.timezone,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": user.timezone,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
                headers={"Authorization": f"Bearer {credentials.token}"},
                json=event,
            )
            response.raise_for_status()
            return response.json()

    async def delete_event(self, user: User, event_id: str):
        credentials = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            response.raise_for_status()

    async def get_events(
        self,
        user: User,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        credentials = Credentials(
            token=user.google_access_token,
            refresh_token=user.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": f"Bearer {credentials.token}"},
                params={
                    "timeMin": start_date.isoformat(),
                    "timeMax": end_date.isoformat(),
                    "singleEvents": True,
                    "orderBy": "startTime",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
