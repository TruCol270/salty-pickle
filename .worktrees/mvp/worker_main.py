"""Standalone worker process that runs APScheduler cron jobs.

Deploy as a separate Railway service with:
  ENABLE_SCHEDULER=true
  (same DATABASE_URL, REDIS_URL, and API keys as the web service)
"""

import asyncio
import logging
import signal

from app.config import get_settings
from app.database import init_db
from app.scheduler.jobs import setup_scheduler, shutdown_scheduler

settings = get_settings()

logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG if settings.debug else logging.INFO,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()
    setup_scheduler()
    logger.info("Worker started — scheduler running")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()
    shutdown_scheduler()
    logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
