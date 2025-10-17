"""Error tracking (Sentry), active only when a DSN is configured.

Kept behind this thin wrapper so the app never imports or calls Sentry
directly: without ``ZENFLOW_SENTRY_DSN`` everything is a no-op and the SDK is
never initialised (fast boot, zero network).
"""
from __future__ import annotations

import logging

import sentry_sdk

from ..config import Settings

logger = logging.getLogger(__name__)

_active = False


def init_sentry(settings: Settings) -> None:
    """Start the Sentry SDK when a DSN is present; otherwise stay inert."""
    global _active
    if not settings.sentry_dsn:
        logger.info("sentry_disabled", extra={"reason": "no ZENFLOW_SENTRY_DSN"})
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        # Our JSON error handlers answer clients; breadcrumbs keep the story
        # without double-reporting handled 4xxs.
        send_default_pii=False,
    )
    _active = True
    logger.info("sentry_enabled", extra={"environment": settings.env})


def capture_exception(error: BaseException) -> None:
    """Report an unexpected exception; no-op until :func:`init_sentry` ran with a DSN."""
    if _active:
        sentry_sdk.capture_exception(error)
