"""Current-user profile routes (read/update/delete the caller's own account)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

users_bp = Blueprint("users", __name__)


@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile() -> Response:
    """Return the caller's profile without the password hash."""
    user = get_services().users.get_profile(get_jwt_identity())
    return api_response(user, 200)


@users_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile() -> Response:
    """Apply whitelisted profile changes and return the refreshed profile."""
    updated = get_services().users.update_profile(get_jwt_identity(), request.get_json())
    return api_response(updated, 200)


@users_bp.route("/profile", methods=["DELETE"])
@jwt_required()
def delete_profile() -> Response:
    """Delete the caller's account document."""
    get_services().users.delete_profile(get_jwt_identity())
    return api_response({"message": "User deleted"}, 200)


@users_bp.route("/profile/settings", methods=["GET"])
@jwt_required()
def get_settings() -> Response:
    """Return the caller's customisation settings (feature 15)."""
    return api_response(get_services().users.get_settings(get_jwt_identity()), 200)


@users_bp.route("/profile/settings", methods=["PUT"])
@jwt_required()
def update_settings() -> Response:
    """Merge theme/fontSize/layout/notificationStyle into preferences."""
    updated = get_services().users.update_settings(
        get_jwt_identity(), request.get_json(silent=True) or {}
    )
    return api_response(updated, 200)
