"""Redis JSON cache helpers (best-effort; failures are ignored)."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()
_client: Optional[redis.Redis] = None


async def _redis() -> Optional[redis.Redis]:
    global _client
    if _client is None:
        try:
            _client = redis.from_url(_settings.redis_url, decode_responses=True)
        except Exception as e:
            logger.warning("Redis unavailable: %s", e)
            return None
    return _client


async def cache_get_json(key: str) -> Optional[Any]:
    try:
        r = await _redis()
        if not r:
            return None
        raw = await r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.debug("cache get miss %s: %s", key, e)
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: int = 120) -> None:
    try:
        r = await _redis()
        if not r:
            return
        await r.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as e:
        logger.debug("cache set failed %s: %s", key, e)


async def cache_delete(key: str) -> None:
    try:
        r = await _redis()
        if not r:
            return
        await r.delete(key)
    except Exception as e:
        logger.debug("cache delete failed %s: %s", key, e)
