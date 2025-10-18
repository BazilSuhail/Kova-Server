"""Local title tidy-up for the smart event title generator (feature 19).

The heuristic runs with no network/key so the endpoint always answers; the LLM
rewrite (``app.utils.llm_utils.generate_title_from_llm``) is applied on top when
a key is configured, falling back here on any provider failure.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

# Word-boundary abbreviation expansions (lower-case keys).
_ABBREVIATIONS = {
    "tmrw": "tomorrow",
    "tmr": "tomorrow",
    "2moro": "tomorrow",
    "2mrw": "tomorrow",
    "tod": "today",
    "asap": "as soon as possible",
    "w/": "with",
    "w": "with",
    "&": "and",
    "mtg": "meeting",
    "appt": "appointment",
}

_ABBREV_RE = re.compile(
    r"\b(" + "|".join(re.escape(key) for key in _ABBREVIATIONS) + r")\b",
    re.IGNORECASE,
)


def tidy_title_locally(raw_title: str) -> str:
    """Expand common abbreviations, collapse spaces, capitalise the first word."""
    text = _ABBREV_RE.sub(lambda m: _ABBREVIATIONS[m.group(1).lower()], raw_title)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return raw_title.strip()
    return text[:1].upper() + text[1:]


def rewrite_title(
    raw_title: str,
    *,
    llm_callable: Callable[[str], str] | None = None,
    use_llm: bool = False,
) -> str:
    """Return a clearer title, using the LLM when asked and available."""
    local = tidy_title_locally(raw_title)
    if not use_llm or llm_callable is None:
        return local
    try:
        value: Any = llm_callable(raw_title)
    except Exception:  # noqa: BLE001 — never block on the provider
        return local
    if isinstance(value, str) and value.strip():
        return value.strip()
    return local
