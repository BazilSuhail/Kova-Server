"""Daily recap route — one thin GET over ``DailyRecapService``.

Renamed from ``dailyRecap.py`` (snake_case) and stripped of the local,
never-registered ``tasks_bp`` that made the legacy endpoint always 500.
"""
from __future__ import annotations

from flask import Blueprint, Response
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

daily_recap_bp = Blueprint("daily-recap", __name__)


@daily_recap_bp.route("/", methods=["GET"])
@jwt_required()
def daily_recap() -> Response:
    """Today's completed/pending tasks and the planner's note for the day."""
    recap = get_services().daily_recap.get_recap(get_jwt_identity())
    return api_response(recap, 200)
