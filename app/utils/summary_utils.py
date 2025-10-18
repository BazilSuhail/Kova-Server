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
from .llm_prompts import NOTES_SUMMARY_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_MIN_BULLETS = 4
_MAX_BULLETS = 9
# Notes path (feature 8): the product spec promises a tighter 3-5 bullets.
_MIN_NOTES_BULLETS = 3
_MAX_NOTES_BULLETS = 5


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


def generate_notes_summary_from_llm(note_text: str) -> list[str]:
    """Summarize raw note text into 3-5 bullet points (feature 8).

    Distinct from the PDF summariser (4-9): the product spec fixes the notes
    path at 3-5. Over-delivery is truncated to 5; under-delivery is an error.

    Raises:
        AIConfigError: no GROQ_API_KEY configured (callers answer 503).
        ValueError: on transport failure or an out-of-range/invalid response.
    """
    content = chat_completion(
        system_prompt=NOTES_SUMMARY_SYSTEM_PROMPT,
        user_content=note_text,
        max_tokens=400,
        temperature=0.4,
    )
    try:
        bullets: Any = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc

    if not isinstance(bullets, list) or not all(
        isinstance(item, str) for item in bullets
    ):
        raise ValueError("LLM response is not a valid list of summary bullets")
    if len(bullets) < _MIN_NOTES_BULLETS:
        raise ValueError("Summary must contain between 3 and 5 bullet points")
    if len(bullets) > _MAX_NOTES_BULLETS:
        logger.warning("llm_notes_summary_truncated", extra={"received": len(bullets)})
        bullets = bullets[:_MAX_NOTES_BULLETS]

    logger.debug("llm_notes_summary_generated", extra={"bullets": len(bullets)})
    return bullets
