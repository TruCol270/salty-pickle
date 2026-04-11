import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = redis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        raw = await r.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception:
        logger.warning("Redis cache get failed for key=%s", key)
    return None


async def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    try:
        r = await get_redis()
        await r.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        logger.warning("Redis cache set failed for key=%s", key)


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception:
        logger.warning("Redis cache delete failed for key=%s", key)
