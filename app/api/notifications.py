from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.notification_service import (
    create_notification,
    get_notifications,
    update_notification
)
from app.utils.api_response import api_response

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not data.get("title") or not data.get("message"):
            return api_response({"message": "Title and message are required"}, 400)

        notification = create_notification(notifications_bp.db, user_id, data)
        return api_response(notification, 201)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@notifications_bp.route("/", methods=["GET"])
@jwt_required()
def list_notifications():
    try:
        user_id = get_jwt_identity()
        notifications = get_notifications(notifications_bp.db, user_id)
        return api_response(notifications, 200)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@notifications_bp.route("/<notification_id>", methods=["PUT"])
@jwt_required()
def update(notification_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        updated = update_notification(notifications_bp.db, notification_id, user_id, data)
        if updated:
            return api_response({"message": "Notification updated"}, 200)
        return api_response({"message": "Notification not found"}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)
