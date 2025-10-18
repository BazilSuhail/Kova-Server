"""Push-device registration routes (feature 10 — reminder delivery)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..core.validation import require_fields
from ..services import get_services

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/", methods=["POST"])
@jwt_required()
def register_device() -> Response:
    """Register (or re-own) an Expo push token for the caller."""
    data = require_fields(
        request.get_json(), "expoPushToken", message="expoPushToken is required"
    )
    return api_response(
        get_services().devices.register(get_jwt_identity(), dict(data)), 201
    )


@devices_bp.route("/", methods=["GET"])
@jwt_required()
def list_devices() -> Response:
    return api_response(get_services().devices.list(get_jwt_identity()), 200)


@devices_bp.route("/<device_id>", methods=["DELETE"])
@jwt_required()
def delete_device(device_id: str) -> Response:
    deleted = get_services().devices.delete(get_jwt_identity(), device_id)
    if deleted:
        return api_response({"message": "Device unregistered"}, 200)
    return api_response({"message": "Device not found"}, 404)
