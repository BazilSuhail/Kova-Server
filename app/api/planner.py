"""Daily planner routes (create/list plans, swap focus & linked tasks, delete)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/", methods=["POST"])
@jwt_required()
def create_planner() -> Response:
    data = request.get_json()
    if not data or "date" not in data:
        return api_response({"message": "Date required"}, 400)
    planner = get_services().planner.create(data, get_jwt_identity())
    return api_response(planner, 201)


@planner_bp.route("/", methods=["GET"])
@jwt_required()
def list_planners() -> Response:
    planners = get_services().planner.list(get_jwt_identity())
    return api_response(planners, 200)


@planner_bp.route("/<planner_id>/focus", methods=["PUT"])
@jwt_required()
def update_focus(planner_id: str) -> Response:
    data = request.get_json()
    if "focusTasks" not in data:
        return api_response({"message": "focusTasks required"}, 400)
    success = get_services().planner.update_focus(
        planner_id, get_jwt_identity(), data["focusTasks"]
    )
    if success:
        return api_response({"message": "Focus tasks updated"}, 200)
    return api_response({"message": "Planner not found"}, 404)


@planner_bp.route("/<planner_id>/tasks", methods=["PUT"])
@jwt_required()
def update_tasks(planner_id: str) -> Response:
    data = request.get_json()
    if "tasks" not in data:
        return api_response({"message": "tasks required"}, 400)
    success = get_services().planner.update_tasks(
        planner_id, get_jwt_identity(), data["tasks"]
    )
    if success:
        return api_response({"message": "Task IDs updated"}, 200)
    return api_response({"message": "Planner not found"}, 404)


@planner_bp.route("/<planner_id>", methods=["PUT"])
@jwt_required()
def update_planner(planner_id: str) -> Response:
    """Update a planner wholesale (whitelisted fields only)."""
    data = request.get_json(silent=True)
    if not data:
        return api_response({"message": "JSON body required"}, 400)
    updated = get_services().planner.update(
        planner_id, get_jwt_identity(), data
    )
    if updated:
        return api_response({"message": "Planner updated"}, 200)
    return api_response({"message": "Planner not found"}, 404)


@planner_bp.route("/<planner_id>", methods=["DELETE"])
@jwt_required()
def delete_planner(planner_id: str) -> Response:
    deleted = get_services().planner.delete(planner_id, get_jwt_identity())
    if deleted:
        return api_response({"message": "Planner deleted"}, 200)
    return api_response({"message": "Planner not found"}, 404)
