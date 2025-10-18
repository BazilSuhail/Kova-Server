"""Shared Groq chat-completions transport used by every AI flow.

One place owns the URL, model, timeout, key guard, and response envelope so
the three domain clients (task fields, subtasks, summary) only do their own
parsing/validation.

Error contract (deliberate):
    * missing ``GROQ_API_KEY`` → :class:`AIConfigError` (503) — a server-side
      misconfiguration must never masquerade as bad client input;
    * transport/shape failure → ``ValueError`` — each flow maps ValueError to
      its historical status (NLP → 400, voice/summary → 500, subtasks → 502),
      so no existing client contract moves.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from flask import current_app

from ..core.exceptions import AIConfigError

logger = logging.getLogger(__name__)

_DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_TIMEOUT_SECONDS = 60


def chat_completion(
    *,
    system_prompt: str,
    user_content: str,
    max_tokens: int,
    temperature: float,
    response_format: dict[str, str] | None = None,
) -> str:
    """Call Groq and return the raw assistant message content.

    Raises:
        AIConfigError: no API key configured (HTTP 503 upstream of callers).
        ValueError: transport failure or an unexpected response shape —
            callers decide the HTTP status, as before.
    """
    api_key = current_app.config.get("GROQ_API_KEY")
    if not api_key:
        logger.error("groq_not_configured")
        raise AIConfigError("AI provider is not configured")

    payload: dict[str, Any] = {
        "model": current_app.config.get("GROQ_MODEL") or _DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout = int(current_app.config.get("LLM_TIMEOUT_SECONDS") or _DEFAULT_TIMEOUT_SECONDS)
    try:
        res = requests.post(
            current_app.config.get("GROQ_LLM_URL") or _DEFAULT_GROQ_URL,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as exc:
        raise ValueError(f"API request failed: {str(exc)}") from exc
    except (KeyError, IndexError) as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc
