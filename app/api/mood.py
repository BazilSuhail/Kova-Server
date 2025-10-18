"""Mood journal routes: log, feed, trends, load suggestions (features 6 & 12)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.exceptions import ValidationError
from ..core.query import parse_page_params
from ..core.responses import api_response
from ..core.validation import require_fields
from ..services import get_services

mood_bp = Blueprint("mood", __name__)


def _days_arg(default: int = 30) -> int:
    raw = request.args.get("days")
    if raw is None:
        return default
    try:
        days = int(raw)
    except ValueError as exc:
        raise ValidationError("days must be an integer") from exc
    if not 1 <= days <= 365:
        raise ValidationError("days must be between 1 and 365")
    return days


@mood_bp.route("/", methods=["POST"])
@jwt_required()
def create_mood() -> Response:
    """Log a mood entry (``mood`` required; ``score``/``energy`` optional)."""
    data = require_fields(request.get_json(), "mood", message="mood is required")
    return api_response(get_services().moods.create(get_jwt_identity(), dict(data)), 201)


@mood_bp.route("/", methods=["GET"])
@jwt_required()
def list_mood() -> Response:
    """Mood log, newest first; ``page``/``limit`` switch to the paged envelope."""
    return api_response(
        get_services().moods.list(
            get_jwt_identity(), page=parse_page_params(request.args)
        ),
        200,
    )


@mood_bp.route("/trends", methods=["GET"])
@jwt_required()
def mood_trends() -> Response:
    """Mood trend series/averages over the last ``days`` (default 30)."""
    return api_response(
        get_services().moods.trends(get_jwt_identity(), days=_days_arg()), 200
    )


@mood_bp.route("/suggestions", methods=["POST"])
@jwt_required()
def mood_suggestions() -> Response:
    """Suggest a task load from the supplied (or latest logged) mood (feature 6)."""
    data = request.get_json(silent=True) or {}
    return api_response(
        get_services().moods.load_suggestion(
            get_jwt_identity(), mood=data.get("mood"), energy=data.get("energy")
        ),
        200,
    )


@mood_bp.route("/<mood_id>", methods=["GET"])
@jwt_required()
def get_mood(mood_id: str) -> Response:
    return api_response(get_services().moods.get(get_jwt_identity(), mood_id), 200)


@mood_bp.route("/<mood_id>", methods=["DELETE"])
@jwt_required()
def delete_mood(mood_id: str) -> Response:
    deleted = get_services().moods.delete(get_jwt_identity(), mood_id)
    if deleted:
        return api_response({"message": "Mood entry deleted"}, 200)
    return api_response({"message": "Mood entry not found"}, 404)
