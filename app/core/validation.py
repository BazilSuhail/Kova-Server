"""Request-body validation shared by routes.

A thin, dependency-free layer so every route rejects malformed payloads the
same way: raise :class:`ValidationError` and let the central handler answer
``400 {"message": ...}``. Messages are passed in by the caller because they
are part of the public contract and must not drift.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .exceptions import ValidationError


def require_fields(
    data: Any,
    *fields: str,
    message: str = "Missing required fields",
    truthy: bool = False,
) -> Mapping[str, Any]:
    """Return ``data`` when it holds every field, else raise a 400.

    Args:
        data: the parsed JSON body (``None`` counts as invalid).
        *fields: field names that must be present.
        message: exact error text the endpoint contract promises.
        truthy: when True each field must also be non-empty (not just present).
    """
    if not isinstance(data, Mapping):
        raise ValidationError(message)
    for field in fields:
        if truthy:
            if not data.get(field):
                raise ValidationError(message)
        elif field not in data:
            raise ValidationError(message)
    return data
