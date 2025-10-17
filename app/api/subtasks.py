"""Subtask routes scoped to a parent task (bulk delete, grouped creation)."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

subtasks_bp = Blueprint("subtasks", __name__)


@subtasks_bp.route("/create", methods=["POST"])
@jwt_required()
def create_subtasks() -> Response:
    data = request.get_json()
    if not data or "taskId" not in data:
        return api_response({"message": "taskId is required"}, 400)
    subtask = get_services().subtasks.create(data, get_jwt_identity(), data["taskId"])
    return api_response(subtask, 201)


@subtasks_bp.route("/task/<task_id>", methods=["GET"])
@jwt_required()
def list_subtasks(task_id: str) -> Response:
    subtasks = get_services().subtasks.list(task_id, get_jwt_identity())
    return api_response(subtasks, 200)


@subtasks_bp.route("/<subtask_id>", methods=["PUT"])
@jwt_required()
def update_subtask(subtask_id: str) -> Response:
    updated = get_services().subtasks.update(
        subtask_id, get_jwt_identity(), request.get_json()
    )
    if updated:
        return api_response({"message": "Subtask updated"}, 200)
    return api_response({"message": "Subtask not found"}, 404)


@subtasks_bp.route("/<subtask_id>", methods=["DELETE"])
@jwt_required()
def delete_subtask(subtask_id: str) -> Response:
    """Delete one subtask; the parent's ``hasSubtasks`` flag follows."""
    deleted = get_services().subtasks.delete_one(
        subtask_id, get_jwt_identity()
    )
    if deleted:
        return api_response({"message": "Subtask deleted"}, 200)
    return api_response({"message": "Subtask not found"}, 404)


@subtasks_bp.route("/task/<task_id>", methods=["DELETE"])
@jwt_required()
def delete_subtasks_for_task(task_id: str) -> Response:
    deleted = get_services().subtasks.delete_for_task(task_id, get_jwt_identity())
    return api_response(
        {"message": f"{deleted} subtask(s) deleted for taskId {task_id}"}, 200
    )
