"""Reflection prompt + journal routes (feature 18)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..core.validation import require_fields
from ..services import get_services

reflections_bp = Blueprint("reflections", __name__)


@reflections_bp.route("/today", methods=["GET"])
@jwt_required()
def today() -> Response:
    """Today's affirmation + reflection prompt, plus the entry if written."""
    return api_response(
        get_services().reflections.today(
            get_jwt_identity(), request.args.get("date")
        ),
        200,
    )


@reflections_bp.route("/", methods=["GET"])
@jwt_required()
def list_reflections() -> Response:
    return api_response(get_services().reflections.list(get_jwt_identity()), 200)


@reflections_bp.route("/", methods=["POST"])
@jwt_required()
def log_reflection() -> Response:
    """Create or replace the day's reflection (``text`` required)."""
    data = require_fields(request.get_json(), "text", message="text is required")
    return api_response(
        get_services().reflections.log(get_jwt_identity(), dict(data)), 201
    )


@reflections_bp.route("/<reflection_id>", methods=["GET"])
@jwt_required()
def get_reflection(reflection_id: str) -> Response:
    return api_response(
        get_services().reflections.get(get_jwt_identity(), reflection_id), 200
    )


@reflections_bp.route("/<reflection_id>", methods=["DELETE"])
@jwt_required()
def delete_reflection(reflection_id: str) -> Response:
    deleted = get_services().reflections.delete(get_jwt_identity(), reflection_id)
    if deleted:
        return api_response({"message": "Reflection deleted"}, 200)
    return api_response({"message": "Reflection not found"}, 404)
