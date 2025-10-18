"""In-process reminder scheduler (APScheduler), started from the app factory.

One background job polls due reminders and delivers them (notification + Expo
push). APScheduler is imported lazily so the app boots even when the optional
dependency is absent, and startup is skipped entirely in tests
(``Settings.for_testing`` disables the scheduler).
"""
from __future__ import annotations

import atexit
import logging
from typing import TYPE_CHECKING

from flask import Flask

from ..config import Settings

if TYPE_CHECKING:
    from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

EXTENSION_KEY = "zenflow.scheduler"


def init_scheduler(app: Flask, settings: Settings) -> BackgroundScheduler | None:
    """Start the reminder-delivery job, or return ``None`` when disabled."""
    if not settings.scheduler_enabled:
        return None
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:  # pragma: no cover - optional dependency
        logger.warning(
            "scheduler_unavailable", extra={"hint": "pip install APScheduler"}
        )
        return None

    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")

    def _tick() -> None:
        with app.app_context():
            from ..services import get_services

            try:
                fired = get_services().reminders.deliver_due()
                if fired:
                    logger.info("reminders_delivered", extra={"count": fired})
            except Exception:  # noqa: BLE001 — one bad tick must not kill the job
                logger.exception("reminder_tick_failed")

    scheduler.add_job(
        _tick,
        "interval",
        seconds=settings.scheduler_interval_seconds,
        id="deliver_reminders",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.start()
    app.extensions[EXTENSION_KEY] = scheduler
    atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)
    logger.info(
        "scheduler_started",
        extra={"interval_seconds": settings.scheduler_interval_seconds},
    )
    return scheduler
