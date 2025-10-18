"""Groq chat-completions client that summarizes extracted PDF text.

Transport lives in :mod:`.groq_client`; this module owns the bullet-shape
validation.  Failures raise ``ValueError`` → the summary flow answers 500
(legacy contract), or ``AIConfigError`` → 503 when no key is configured.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .groq_client import chat_completion
from .llm_prompts import SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_MIN_BULLETS = 4
_MAX_BULLETS = 9


def generate_summary_from_llm(extracted_text: str) -> list[str]:
    """Return 4–9 bullet points summarizing ``extracted_text``.

    Raises:
        AIConfigError: no GROQ_API_KEY configured (callers answer 503).
        ValueError: on transport failure, a non-array response, or a bullet
            count outside 4–9 — callers decide the HTTP status.
    """
    content = chat_completion(
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        user_content=extracted_text,
        max_tokens=500,
        temperature=0.5,
    )
    try:
        summary_bullets: Any = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc

    if not isinstance(summary_bullets, list) or not all(
        isinstance(item, str) for item in summary_bullets
    ):
        raise ValueError("LLM response is not a valid list of summary bullets")
    if not (_MIN_BULLETS <= len(summary_bullets) <= _MAX_BULLETS):
        raise ValueError("Summary must contain between 4 and 9 bullet points")

    logger.debug("llm_summary_generated", extra={"bullets": len(summary_bullets)})
    return summary_bullets
