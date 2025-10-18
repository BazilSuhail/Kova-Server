"""Smart reminder scheduling routes (feature 10)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..core.validation import require_fields
from ..services import get_services

reminders_bp = Blueprint("reminders", __name__)


@reminders_bp.route("/", methods=["POST"])
@jwt_required()
def create_reminder() -> Response:
    """Schedule a reminder (``title`` + ``fireAt`` required)."""
    data = require_fields(
        request.get_json(),
        "title",
        "fireAt",
        message="title and fireAt are required",
    )
    return api_response(
        get_services().reminders.create(get_jwt_identity(), dict(data)), 201
    )


@reminders_bp.route("/", methods=["GET"])
@jwt_required()
def list_reminders() -> Response:
    """All reminders, soonest first; optional ``?status=pending|sent``."""
    return api_response(
        get_services().reminders.list(
            get_jwt_identity(), status=request.args.get("status")
        ),
        200,
    )


@reminders_bp.route("/upcoming", methods=["GET"])
@jwt_required()
def upcoming_reminders() -> Response:
    """Pending reminders in the next ``hours`` (default 48)."""
    raw = request.args.get("hours", "48")
    try:
        hours = int(raw)
    except ValueError:
        hours = 48
    return api_response(
        get_services().reminders.upcoming(get_jwt_identity(), hours=hours), 200
    )


@reminders_bp.route("/<reminder_id>", methods=["GET"])
@jwt_required()
def get_reminder(reminder_id: str) -> Response:
    return api_response(
        get_services().reminders.get(get_jwt_identity(), reminder_id), 200
    )


@reminders_bp.route("/<reminder_id>", methods=["DELETE"])
@jwt_required()
def delete_reminder(reminder_id: str) -> Response:
    deleted = get_services().reminders.delete(get_jwt_identity(), reminder_id)
    if deleted:
        return api_response({"message": "Reminder deleted"}, 200)
    return api_response({"message": "Reminder not found"}, 404)
