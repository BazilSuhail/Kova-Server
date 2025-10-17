"""Notification routes (create, feed, single read, mark-as-read, delete)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.query import parse_bool_arg, parse_page_params
from ..core.responses import api_response
from ..services import get_services

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/", methods=["POST"])
@jwt_required()
def create_notification() -> Response:
    data = request.get_json()
    if not data or not data.get("title") or not data.get("message"):
        return api_response({"message": "Title and message are required"}, 400)
    notification = get_services().notifications.create(get_jwt_identity(), data)
    return api_response(notification, 201)


@notifications_bp.route("/", methods=["GET"])
@jwt_required()
def list_notifications() -> Response:
    """Feed listing; optional ``unread=true|false`` filter and ``page``/``limit``."""
    notifications = get_services().notifications.list(
        get_jwt_identity(),
        unread=parse_bool_arg(request.args, "unread"),
        page=parse_page_params(request.args),
    )
    return api_response(notifications, 200)


@notifications_bp.route("/<notification_id>", methods=["GET"])
@jwt_required()
def get_notification(notification_id: str) -> Response:
    notification = get_services().notifications.get(
        notification_id, get_jwt_identity()
    )
    if notification is None:
        return api_response({"message": "Notification not found"}, 404)
    return api_response(notification, 200)


@notifications_bp.route("/<notification_id>", methods=["PUT"])
@jwt_required()
def update_notification(notification_id: str) -> Response:
    updated = get_services().notifications.update(
        notification_id, get_jwt_identity(), request.get_json()
    )
    if updated:
        return api_response({"message": "Notification updated"}, 200)
    return api_response({"message": "Notification not found"}, 404)


@notifications_bp.route("/<notification_id>", methods=["DELETE"])
@jwt_required()
def delete_notification(notification_id: str) -> Response:
    deleted = get_services().notifications.delete(
        notification_id, get_jwt_identity()
    )
    if deleted:
        return api_response({"message": "Notification deleted"}, 200)
    return api_response({"message": "Notification not found"}, 404)
