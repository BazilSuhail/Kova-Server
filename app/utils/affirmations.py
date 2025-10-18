"""Curated daily affirmations and reflection prompts (feature 18).

Deterministic by date so the same day always shows the same content (no network,
no API key, cache-friendly on the client).
"""
from __future__ import annotations

from datetime import date

AFFIRMATIONS: tuple[str, ...] = (
    "You do not have to finish everything today; you only have to begin.",
    "Small steps, taken consistently, become the path.",
    "Rest is part of the work, not a reward for it.",
    "Progress, not perfection, is the goal today.",
    "You are allowed to do things at your own pace.",
    "One honest hour beats a scattered day.",
    "Your worth is not measured by your task list.",
    "Choose the next small thing, then the next.",
    "Focus on what is within your control.",
    "You have handled harder days than this.",
)

PROMPTS: tuple[str, ...] = (
    "What is one thing that went well today?",
    "What drained your energy, and what gave it back?",
    "What would make tomorrow feel like a win?",
    "What are you most grateful for right now?",
    "Where did you show up for yourself today?",
    "What is one thing you can let go of?",
    "Who or what supported you today?",
    "What did you learn about how you work best?",
)


def _index_for(day: str, size: int) -> int:
    """Stable index from a ``YYYY-MM-DD`` string (days since epoch)."""
    try:
        ordinal = date.fromisoformat(day).toordinal()
    except ValueError:
        ordinal = date.today().toordinal()
    return ordinal % size


def affirmation_for(day: str) -> str:
    return AFFIRMATIONS[_index_for(day, len(AFFIRMATIONS))]


def prompt_for(day: str) -> str:
    return PROMPTS[_index_for(day, len(PROMPTS))]
