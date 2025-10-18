"""Groq chat-completions client for structured task extraction.

Transport lives in :mod:`.groq_client`; this module owns the task-shape
validation.  Failures raise ``ValueError`` (the NLP route maps it to 400 —
legacy contract) or ``AIConfigError`` (503, missing key).
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .groq_client import chat_completion
from .llm_prompts import TASK_FIELDS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ("title", "description", "category", "dueDate", "createdFrom")


def generate_task_fields_from_llm(transcript: str) -> dict[str, Any]:
    """Turn free text (prompt or transcript) into task fields via Groq.

    Returns:
        dict with title/description/category/dueDate/createdFrom, all strings.

    Raises:
        AIConfigError: no GROQ_API_KEY configured (callers answer 503).
        ValueError: on transport failure or a malformed LLM response.
    """
    content = chat_completion(
        system_prompt=TASK_FIELDS_SYSTEM_PROMPT,
        user_content=transcript,
        max_tokens=200,
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    try:
        result: Any = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc

    if not isinstance(result, dict) or not all(
        field in result for field in _REQUIRED_FIELDS
    ):
        raise ValueError("LLM response missing required fields")
    # Type guard: a hallucinated non-string ({"title": 3}) would be persisted
    # verbatim and break clients rendering task fields.
    for field in _REQUIRED_FIELDS:
        if not isinstance(result[field], str):
            raise ValueError(f"LLM field '{field}' is not a string")

    logger.debug("llm_task_fields_extracted", extra={"fields": list(result)})
    return result
