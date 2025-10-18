"""Calendar view route: day/week/month (feature 5)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/", methods=["GET"])
@jwt_required()
def calendar() -> Response:
    """Tasks + planner per day for ``?view=day|week|month`` (default week)."""
    return api_response(
        get_services().calendar.get(
            get_jwt_identity(),
            view=request.args.get("view", "week"),
            day=request.args.get("date"),
        ),
        200,
    )
