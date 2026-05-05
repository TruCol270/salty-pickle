import logging
import re
import sys
import time
from collections.abc import Callable

import sentry_sdk
import structlog
from fastapi import Request

SENSITIVE_KEYS = re.compile(
    r"(authorization|cookie|token|secret|password|api[_-]?key|client[_-]?secret)",
    re.IGNORECASE,
)


def _scrub(value):
    if isinstance(value, dict):
        return {
            key: "[Filtered]" if SENSITIVE_KEYS.search(str(key)) else _scrub(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def before_send(event, hint):
    event = _scrub(event)
    request = event.get("request")
    if isinstance(request, dict):
        for key in ("headers", "cookies", "data", "query_string"):
            if key in request:
                request[key] = _scrub(request[key])
    return event


def configure_logging(log_level: str, debug: bool) -> None:
    level_name = (log_level or ("DEBUG" if debug else "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def init_sentry(*, dsn: str, environment: str, release: str) -> None:
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=environment or None,
        release=release or None,
        before_send=before_send,
        send_default_pii=False,
        traces_sample_rate=0.0,
    )


def request_logger() -> Callable:
    logger = structlog.get_logger("salty_pickle.requests")

    async def middleware(request: Request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "request_error",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    return middleware
