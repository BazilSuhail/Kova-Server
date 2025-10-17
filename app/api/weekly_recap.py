"""Weekly recap route — one thin GET over ``WeeklyRecapService``."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

weekly_recap_bp = Blueprint("weekly-recap", __name__)


@weekly_recap_bp.route("/", methods=["GET"])
@jwt_required()
def weekly_recap() -> Response:
    """Rolling 7-day recap; optional ``?end=YYYY-MM-DD`` (default: today, UTC)."""
    recap = get_services().weekly_recap.get_recap(
        get_jwt_identity(), request.args.get("end")
    )
    return api_response(recap, 200)
