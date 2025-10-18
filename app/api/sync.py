"""Offline sync routes: delta pull + last-write-wins push (feature 14)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

sync_bp = Blueprint("sync", __name__)


@sync_bp.route("/pull", methods=["POST"])
@jwt_required()
def pull() -> Response:
    """Return everything changed since ``since`` plus deleted ids.

    Body: ``{"since": "<iso timestamp>"}`` (omit/``null`` for a full sync).
    """
    data = request.get_json(silent=True) or {}
    return api_response(
        get_services().sync.pull(get_jwt_identity(), data.get("since")), 200
    )


@sync_bp.route("/push", methods=["POST"])
@jwt_required()
def push() -> Response:
    """Apply offline changes (per-collection arrays + ``deletions``)."""
    data = request.get_json(silent=True) or {}
    changes = data.get("changes", data)
    return api_response(get_services().sync.push(get_jwt_identity(), changes), 200)
