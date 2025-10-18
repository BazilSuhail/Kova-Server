"""Adaptive suggestions route (feature 17)."""
from __future__ import annotations

from flask import Blueprint, Response
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

suggestions_bp = Blueprint("suggestions", __name__)


@suggestions_bp.route("/", methods=["GET"])
@jwt_required()
def suggestions() -> Response:
    """Habit-aware suggestions derived from tasks, moods, and reminders."""
    return api_response(get_services().suggestions.get(get_jwt_identity()), 200)
