"""Current-user profile routes (read/update/delete the caller's own account)."""
from __future__ import annotations

from flask import Blueprint, Response, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.exceptions import NotFoundError
from ..core.responses import api_response
from ..services import get_services
from ..utils import avatars

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


@users_bp.route("/avatars", methods=["GET"])
def list_avatars() -> Response:
    """Catalogue of selectable, server-hosted avatars (feature 15)."""
    return api_response({"avatars": avatars.list_avatars()}, 200)


@users_bp.route("/avatars/<path:filename>", methods=["GET"])
def get_avatar(filename: str) -> Response:
    """Serve one avatar image.

    Public on purpose: avatars are non-sensitive static assets, so a mobile
    ``<Image>`` can render them without attaching an Authorization header.
    """
    path = avatars.avatar_file(filename)
    if path is None:
        raise NotFoundError("Avatar not found")
    return send_from_directory(str(path.parent), path.name)
