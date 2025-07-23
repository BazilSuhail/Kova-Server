from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.notification_service import create_notification, get_notifications, update_notification, delete_notification
from ..utils import api_response

notifications_bp = Blueprint("notifications", __name__)

@notifications_bp.route("/", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not all(key in data for key in ["title", "message"]):
            return api_response({"message": "Title and message required"}, 400)
        notification = create_notification(data, user_id)
        return api_response(notification, 201)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@notifications_bp.route("/", methods=["GET"])
@jwt_required()
def list_notifications():
    try:
        user_id = get_jwt_identity()
        notifications = get_notifications(user_id)
        return api_response(notifications, 200)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@notifications_bp.route("/<notification_id>", methods=["PUT"])
@jwt_required()
def update(notification_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if update_notification(notification_id, user_id, data):
            return api_response({"message": "Notification updated"}, 200)
        return api_response({"message": "Notification not found"}, 404)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@notifications_bp.route("/<notification_id>", methods=["DELETE"])
@jwt_required()
def delete(notification_id):
    try:
        user_id = get_jwt_identity()
        if delete_notification(notification_id, user_id):
            return api_response({"message": "Notification deleted"}, 200)
        return api_response({"message": "Notification not found"}, 404)
    except Exception:
        return api_response({"message": "Server error"}, 500)