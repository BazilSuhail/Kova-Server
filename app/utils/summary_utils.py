"""Groq chat-completions client that summarizes extracted PDF text."""
from __future__ import annotations

import json
import logging
from typing import Any

import requests
from flask import current_app

from .llm_prompts import SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def generate_summary_from_llm(extracted_text: str) -> list[str]:
    """Return 4–9 bullet points summarizing ``extracted_text``.

    Raises:
        ValueError: on transport failure, a non-array response, or a bullet
            count outside 4–9 — callers decide the HTTP status.
    """
    groq_api_key = current_app.config["GROQ_API_KEY"]
    groq_llm_url = current_app.config.get("GROQ_LLM_URL", _DEFAULT_GROQ_URL)

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": extracted_text},
        ],
        "max_tokens": 500,
        "temperature": 0.5,
    }
    headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}

    try:
        res = requests.post(groq_llm_url, json=payload, headers=headers, timeout=60)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        summary_bullets: Any = json.loads(content)
    except requests.exceptions.RequestException as exc:
        raise ValueError(f"API request failed: {str(exc)}") from exc
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc

    if not isinstance(summary_bullets, list) or not all(
        isinstance(item, str) for item in summary_bullets
    ):
        raise ValueError("LLM response is not a valid list of summary bullets")
    if not (4 <= len(summary_bullets) <= 9):
        raise ValueError("Summary must contain between 4 and 9 bullet points")

    logger.debug("llm_summary_generated", extra={"bullets": len(summary_bullets)})
    return summary_bullets
