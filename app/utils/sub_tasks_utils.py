"""Groq chat-completions client that breaks a task description into sub-tasks.

Transport lives in :mod:`.groq_client`.  The prompt promises 3–8 ordered items;
a model that over-delivers is truncated to the first 8 (already in logical
order) rather than failing a usable response.  Under-delivery or a non-array
answer raises ``ValueError`` → the subtask service answers 502.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .groq_client import chat_completion
from .llm_prompts import SUBTASKS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_MIN_SUBTASKS = 3
_MAX_SUBTASKS = 8


def generate_subtasks_from_description(task_description: str) -> list[str]:
    """Split a task description into 3–8 ordered, actionable sub-task strings.

    Renamed from ``make_subTasks_from_tasks_description`` (snake_case).

    Raises:
        AIConfigError: no GROQ_API_KEY configured (callers answer 503).
        ValueError: on transport failure, a non-array response, or fewer than
            3 items — callers decide the HTTP status.
    """
    content = chat_completion(
        system_prompt=SUBTASKS_SYSTEM_PROMPT,
        user_content=task_description,
        max_tokens=500,
        temperature=0.3,
    )
    try:
        subtasks: Any = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc

    if not isinstance(subtasks, list) or not all(isinstance(item, str) for item in subtasks):
        raise ValueError("LLM response is not a valid list of sub-tasks")
    if len(subtasks) < _MIN_SUBTASKS:
        raise ValueError("Sub-tasks must contain between 3 and 8 items")
    if len(subtasks) > _MAX_SUBTASKS:
        logger.warning(
            "llm_subtasks_truncated", extra={"received": len(subtasks)}
        )
        subtasks = subtasks[:_MAX_SUBTASKS]

    logger.debug("llm_subtasks_generated", extra={"count": len(subtasks)})
    return subtasks
