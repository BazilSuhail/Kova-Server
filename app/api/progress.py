"""Personal progress route: totals, streaks, load balance, achievements (13)."""
from __future__ import annotations

from flask import Blueprint, Response
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

progress_bp = Blueprint("progress", __name__)


@progress_bp.route("/", methods=["GET"])
@jwt_required()
def progress() -> Response:
    """Derived progress summary for the caller (no stored aggregates)."""
    return api_response(get_services().progress.get_summary(get_jwt_identity()), 200)
