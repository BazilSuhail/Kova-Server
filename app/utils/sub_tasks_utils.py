"""Groq chat-completions client that breaks a task description into sub-tasks."""
from __future__ import annotations

import json
import logging
from typing import Any

import requests
from flask import current_app

from .llm_prompts import SUBTASKS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_DEFAULT_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def generate_subtasks_from_description(task_description: str) -> list[str]:
    """Split a task description into 3–8 ordered, actionable sub-task strings.

    Renamed from ``make_subTasks_from_tasks_description`` (snake_case).

    Raises:
        ValueError: on transport failure, a non-array response, or an
            out-of-range item count — callers decide the HTTP status.
    """
    groq_api_key = current_app.config["GROQ_API_KEY"]
    groq_llm_url = current_app.config.get("GROQ_LLM_URL", _DEFAULT_GROQ_URL)

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SUBTASKS_SYSTEM_PROMPT},
            {"role": "user", "content": task_description},
        ],
        "max_tokens": 500,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}

    try:
        res = requests.post(groq_llm_url, json=payload, headers=headers, timeout=60)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        subtasks: Any = json.loads(content)
    except requests.exceptions.RequestException as exc:
        raise ValueError(f"API request failed: {str(exc)}") from exc
    except (KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse LLM response: {str(exc)}") from exc

    if not isinstance(subtasks, list) or not all(isinstance(item, str) for item in subtasks):
        raise ValueError("LLM response is not a valid list of sub-tasks")
    if not (3 <= len(subtasks) <= 20):
        raise ValueError("Sub-tasks must contain between 3 and 8 items")

    logger.debug("llm_subtasks_generated", extra={"count": len(subtasks)})
    return subtasks
