"""Home dashboard aggregation route (feature 2)."""
from __future__ import annotations

from flask import Blueprint, Response
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
@jwt_required()
def dashboard() -> Response:
    """One call for the home screen: task counts, today, reminders, unread."""
    return api_response(get_services().dashboard.get(get_jwt_identity()), 200)
