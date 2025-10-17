"""The single serializer every endpoint uses so response shapes never drift.

Replaces ``app/utils/api_response.py`` (and the shadowed legacy ``app/utils.py``)
with an identical implementation: ``ObjectId`` and ``datetime`` values are
converted to JSON-safe primitives before ``jsonify``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId
from flask import Response, jsonify


def _serialize(obj: Any) -> Any:
    """Recursively convert Mongo/datetime values into JSON-safe primitives."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {key: _serialize(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    return obj


def api_response(data: Any, status_code: int) -> Response:
    """Return ``data`` as JSON with ``status_code`` (ObjectId/datetime aware)."""
    response = jsonify(_serialize(data))
    response.status_code = status_code
    return response
