"""Groq chat-completions client for structured task extraction.

All failures are raised as ``ValueError`` because that is the contract the
callers (task routes/services) translate into 400/500 responses.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import requests
from flask import current_app

from .llm_prompts import TASK_FIELDS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_REQUIRED_FIELDS = ("title", "description", "category", "dueDate", "createdFrom")


def generate_task_fields_from_llm(transcript: str) -> dict[str, Any]:
    """Turn free text (prompt or transcript) into task fields via Groq.

    Returns:
        dict with title/description/category/dueDate/createdFrom.

    Raises:
        ValueError: on transport failure or a malformed LLM response.
    """
    groq_api_key = current_app.config["GROQ_API_KEY"]
    groq_llm_url = current_app.config.get("GROQ_LLM_URL", _DEFAULT_GROQ_URL)

    payload: dict[str, Any] = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": TASK_FIELDS_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        "max_tokens": 200,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}

    try:
        res = requests.post(groq_llm_url, json=payload, headers=headers, timeout=60)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
    except requests.exceptions.RequestException as exc:
        raise ValueError(f"API request failed: {str(exc)}") from exc
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc

    if not all(field in result for field in _REQUIRED_FIELDS):
        raise ValueError("LLM response missing required fields")

    logger.debug("llm_task_fields_extracted", extra={"fields": list(result)})
    return result
