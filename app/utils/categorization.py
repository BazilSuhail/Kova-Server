"""Local keyword categoriser for smart task categorisation (feature 4).

Deliberately offline-first: a manual task is labelled without any network call
or API key, so ``POST /api/tasks/`` keeps working in tests and without Groq.
The LLM path (used by the NLP/voice flows) still returns a category upstream.
"""
from __future__ import annotations

from typing import Any

CATEGORIES = (
    "academics",
    "work",
    "personal",
    "health",
    "social",
    "finance",
    "errands",
    "other",
)

# Ordered keyword → category map. First match wins, so put specific ahead of broad.
_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "academics": (
        "study", "exam", "homework", "assignment", "lecture", "thesis", "course",
        "class", "revision", "revise", "quiz", "semester", "university", "college",
        "research", "essay", "dissertation", "tutorial", "grade", "professor",
    ),
    "work": (
        "meeting", "email", "client", "deadline", "report", "presentation",
        "invoice", "standup", "sprint", "office", "boss", "manager", "deploy",
        "review pr", "pull request", "interview", "onboarding", "timesheet",
    ),
    "health": (
        "gym", "workout", "run", "doctor", "dentist", "medicine", "medication",
        "sleep", "yoga", "meditation", "workout", "hospital", "therapy",
        "appointment", "checkup", "vitamin", "hydrate", "steps",
    ),
    "social": (
        "call mom", "call dad", "friend", "birthday", "party", "dinner with",
        "catch up", "wedding", "hangout", "coffee with", "meet up", "reunion",
        "anniversary", "visit",
    ),
    "finance": (
        "bill", "budget", "rent", "bank", "tax", "subscription", "pay ", "payment",
        "salary", "refund", "loan", "credit card", "insurance", "invest",
    ),
    "errands": (
        "buy", "grocery", "groceries", "milk", "shop", "shopping", "pick up",
        "pickup", "post office", "laundry", "clean", "tidy", "return package",
        "pharmacy", "gas", "fuel",
    ),
    "personal": (
        "read", "journal", "hobby", "travel", "trip", "plan", "reflect", "write",
        "paint", "guitar", "practice", "learn", "course", "meditate",
    ),
}


def categorize_locally(title: str, description: str = "") -> str:
    """Best-effort category from keywords; ``other`` when nothing matches."""
    text = f"{title} {description}".lower()
    best_category = "other"
    best_score = 0
    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_category, best_score = category, score
    return best_category


def categorize_task(
    title: str,
    description: str = "",
    *,
    llm_callable: Any = None,
    use_llm: bool = False,
) -> str:
    """Return a category, optionally refined by an LLM when one is configured.

    Any LLM failure falls back to the deterministic local result so a task is
    never blocked on the provider (feature 4 must degrade, not 500).
    """
    local = categorize_locally(title, description)
    if not use_llm or llm_callable is None:
        return local
    try:
        value = llm_callable(title, description)
    except Exception:  # noqa: BLE001 — provider failures must not break the flow
        return local
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return local
