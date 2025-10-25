"""The caller's local timezone, from the ``X-Timezone`` request header.

"Today" and day boundaries (dashboard, recaps, calendar, streaks, mood dates)
are computed in the user's zone; absolute instants stay in UTC.
"""
from __future__ import annotations

from datetime import UTC, datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import has_request_context, request

HEADER = "X-Timezone"


def request_tz() -> tzinfo:
    """Validated IANA zone from the header; missing/invalid (or no request) → UTC."""
    if not has_request_context():
        return UTC
    name = (request.headers.get(HEADER) or "").strip()
    if not name or len(name) > 64:
        return UTC
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return UTC


def local_now() -> datetime:
    """Aware "now" in the caller's zone (use ``.date()`` for their today)."""
    return datetime.now(request_tz())
