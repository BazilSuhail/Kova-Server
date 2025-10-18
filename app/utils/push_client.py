"""Expo push delivery for scheduled reminders and nudges (feature 10).

Failures are logged, never raised: the scheduler must not crash a tick because
a provider hiccupped. Expo reports per-token errors in the ticket list; tokens
reported as ``DeviceNotRegistered`` are surfaced to the caller so the reminder
service can prune them.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from flask import current_app

logger = logging.getLogger(__name__)

_DEFAULT_PUSH_URL = "https://exp.host/--/api/v2/push/send"
_STALE_TICKET_ERRORS = frozenset({"DeviceNotRegistered"})


def send_push(messages: list[dict[str, Any]]) -> list[str]:
    """Send a batch of Expo push messages; return tokens that are now invalid.

    Args:
        messages: Expo message objects (must include ``to``).

    Returns:
        Tokens Expo flagged as unregistered. Empty when push is disabled, the
        batch is empty, or the provider call failed (logged, not raised).
    """
    if not messages or not current_app.config.get("PUSH_ENABLED", True):
        return []

    url = current_app.config.get("PUSH_URL") or _DEFAULT_PUSH_URL
    headers = {"Content-Type": "application/json"}
    access_token = current_app.config.get("PUSH_ACCESS_TOKEN")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        response = requests.post(url, json=messages, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        logger.warning("push_send_failed", extra={"error": str(exc)})
        return []

    tickets = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(tickets, list):
        return []

    stale: list[str] = []
    for message, ticket in zip(messages, tickets, strict=False):
        details = (ticket or {}).get("details") or {}
        if details.get("error") in _STALE_TICKET_ERRORS:
            stale.append(message.get("to", ""))
    if stale:
        logger.info("push_stale_tokens", extra={"count": len(stale)})
    return stale
