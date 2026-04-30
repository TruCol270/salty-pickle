import logging
from datetime import datetime, timedelta
from typing import Optional
import hmac
import hashlib

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User

settings = get_settings()
logger = logging.getLogger(__name__)

# Whoop sends webhook events for these types
WHOOP_WEBHOOK_EVENTS = [
    "recovery.updated",
    "sleep.updated",
    "workout.updated",
]


class WhoopService:
    AUTH_BASE = "https://api.prod.whoop.com/oauth/oauth2"
    API_BASE = "https://api.prod.whoop.com/developer/v2"

    SCOPES = [
        "read:recovery",
        "read:cycles",
        "read:workout",
        "read:sleep",
        "read:profile",
        "offline",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_authorization_url(self, state: str) -> str:
        from urllib.parse import urlencode

        params = {
            "client_id": settings.whoop_client_id,
            "redirect_uri": settings.whoop_redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
        }
        return f"{self.AUTH_BASE}/auth?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.AUTH_BASE}/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.whoop_client_id,
                    "client_secret": settings.whoop_client_secret,
                    "code": code,
                    "redirect_uri": settings.whoop_redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.AUTH_BASE}/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": settings.whoop_client_id,
                    "client_secret": settings.whoop_client_secret,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_current_user(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/user/profile/basic",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_recovery(
        self,
        access_token: str,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_BASE}/recovery",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "start": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "end": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "limit": 1,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("records", [])

    async def get_latest_recovery(self, user: User) -> Optional[dict]:
        if not user.whoop_access_token:
            return None

        try:
            records = await self.get_recovery(
                user.whoop_access_token,
                datetime.utcnow() - timedelta(days=7),
                datetime.utcnow(),
            )

            if records:
                latest = records[0]
                score = latest.get("score", {})
                return {
                    "recovery_score": score.get("recovery_score", 0) / 100,
                    "resting_heart_rate": score.get("resting_heart_rate"),
                    "hrv_rmssd_milli": score.get("hrv_rmssd_milli"),
                    "spo2_percentage": score.get("spo2_percentage"),
                    "skin_temp_celsius": score.get("skin_temp_celsius"),
                    "cycle_id": latest.get("cycle_id"),
                    "created_at": latest.get("created_at"),
                }
        except Exception as e:
            logger.exception("Failed to get Whoop recovery: %s", e)

        return None

    async def get_recovery_history(self, user: User, days: int = 7) -> list[dict]:
        """Recent recovery points for charts (newest last)."""
        if not user.whoop_access_token:
            return []
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_BASE}/recovery",
                    headers={"Authorization": f"Bearer {user.whoop_access_token}"},
                    params={
                        "start": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "end": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "limit": 25,
                    },
                )
                response.raise_for_status()
                records = response.json().get("records", [])
        except Exception as e:
            logger.warning("Whoop recovery history fetch failed: %s", e)
            return []

        points: list[dict] = []
        for rec in records:
            score = rec.get("score", {}) or {}
            raw = score.get("recovery_score")
            if raw is None:
                continue
            rf = float(raw)
            recovery_pct = rf * 100.0 if rf <= 1.0 else rf
            created = rec.get("created_at") or rec.get("updated_at") or ""
            label = ""
            try:
                if isinstance(created, str) and created:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    label = dt.strftime("%a")
                else:
                    label = str(len(points))
            except (ValueError, TypeError):
                label = str(len(points))
            points.append(
                {
                    "label": label,
                    "recovery": round(recovery_pct, 1),
                    "hrv": score.get("hrv_rmssd_milli"),
                    "rhr": score.get("resting_heart_rate"),
                }
            )
        # Oldest → newest for left-to-right chart
        return list(reversed(points))

    async def get_recovery_recommendation(self, recovery_data: dict) -> str:
        if not recovery_data:
            return "maintain"

        # recovery_score is 0.0-1.0 (already divided by 100)
        recovery_score = recovery_data.get("recovery_score", 0.5)

        if recovery_score >= 0.66:
            return "push"
        elif recovery_score >= 0.33:
            return "maintain"
        elif recovery_score >= 0.2:
            return "easy"
        else:
            return "rest"

    async def register_webhook(self, callback_url: str) -> dict:
        """Register a webhook subscription with Whoop."""
        import base64

        credentials = base64.b64encode(
            f"{settings.whoop_client_id}:{settings.whoop_client_secret}".encode()
        ).decode()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.prod.whoop.com/webhook/v1",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": callback_url,
                    "event_types": WHOOP_WEBHOOK_EVENTS,
                },
            )
            response.raise_for_status()
            return response.json()

    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook subscription."""
        import base64

        credentials = base64.b64encode(
            f"{settings.whoop_client_id}:{settings.whoop_client_secret}".encode()
        ).decode()
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"https://api.prod.whoop.com/webhook/v1/{webhook_id}",
                headers={"Authorization": f"Basic {credentials}"},
            )
            response.raise_for_status()

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the webhook payload came from Whoop."""
        expected = hmac.new(
            settings.whoop_client_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def parse_recovery_event(self, payload: dict) -> Optional[dict]:
        """Parse a Whoop recovery webhook payload into our format."""
        data = payload.get("data", {})
        if not data:
            return None

        score = data.get("score", {})
        recovery_score = score.get("recovery_score", 0) / 100
        sleep_performance = score.get("sleep_performance_percentage", 0) / 100

        return {
            "recovery_score": recovery_score,
            "sleep_performance": sleep_performance,
            "resting_heart_rate": score.get("resting_heart_rate"),
            "hrv_rmssd_milli": score.get("hrv_rmssd_milli"),
            "cycle_id": data.get("cycle_id"),
            "cycle_date": data.get("created_at"),
            "user_id": payload.get("user_id"),
            "spo2_percentage": score.get("spo2_percentage"),
            "skin_temp_celsius": score.get("skin_temp_celsius"),
        }
