"""Optional offset pagination + query-arg parsing shared by list endpoints.

Contract: a request *without* ``page``/``limit`` keeps the legacy bare-array
response untouched; supplying either switches the body to
``{"items": [...], "pagination": {...}}`` so existing clients only see a
different shape once they opt in to paging.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .exceptions import ValidationError

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PageParams:
    """Validated ``page``/``limit`` pair (1-based page index)."""

    page: int
    limit: int

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


def _positive_int(raw: str | None, name: str, default: int) -> int:
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} must be an integer") from exc
    if value < 1:
        raise ValidationError(f"{name} must be at least 1")
    return value


def parse_page_params(args: Mapping[str, str]) -> PageParams | None:
    """Parse ``page``/``limit``; ``None`` when neither is present (legacy list)."""
    if args.get("page") is None and args.get("limit") is None:
        return None
    page = _positive_int(args.get("page"), "page", 1)
    limit = _positive_int(args.get("limit"), "limit", DEFAULT_PAGE_SIZE)
    if limit > MAX_PAGE_SIZE:
        raise ValidationError(f"limit must be at most {MAX_PAGE_SIZE}")
    return PageParams(page=page, limit=limit)


def parse_bool_arg(args: Mapping[str, str], name: str) -> bool | None:
    """Parse a boolean query arg; ``None`` when absent."""
    raw = args.get(name)
    if raw is None:
        return None
    value = raw.strip().lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    raise ValidationError(f"{name} must be true or false")


def page_payload(
    items: list[dict[str, Any]], total: int, params: PageParams
) -> dict[str, Any]:
    """Envelope for an opted-in paged response."""
    total_pages = max(1, (total + params.limit - 1) // params.limit)
    return {
        "items": items,
        "pagination": {
            "page": params.page,
            "limit": params.limit,
            "total": total,
            "totalPages": total_pages,
            "hasNext": params.page < total_pages,
            "hasPrev": params.page > 1,
        },
    }
