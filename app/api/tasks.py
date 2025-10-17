"""Task routes: manual, natural-language, and voice creation plus CRUD.

All validation that depends on the *request shape* happens here; everything
that depends on stored state happens in ``TaskService``.
"""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/", methods=["POST"])
@jwt_required()
def create_task() -> Response:
    data = request.get_json()
    if not data or "title" not in data:
        return api_response({"message": "Title required"}, 400)
    task = get_services().tasks.create(data, get_jwt_identity())
    return api_response(task, 201)


@tasks_bp.route("/create/natural-language", methods=["POST"])
@jwt_required()
def create_task_from_natural_language() -> Response:
    if not request.is_json:
        return api_response({"message": "Request must be JSON"}, 415)
    data = request.get_json()
    if not data or "prompt" not in data:
        return api_response({"message": "prompt is required in JSON body"}, 400)
    task = get_services().tasks.create_from_natural_language(
        get_jwt_identity(), data["prompt"]
    )
    return api_response(task, 201)


@tasks_bp.route("/create/voice", methods=["POST"])
@jwt_required()
def create_task_from_voice() -> Response:
    if "file" not in request.files:
        return api_response({"message": "Audio file is required."}, 400)
    file = request.files["file"]
    task = get_services().tasks.create_from_voice(get_jwt_identity(), file.stream)
    return api_response(task, 201)


@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks() -> Response:
    tasks = get_services().tasks.list(get_jwt_identity())
    return api_response(tasks, 200)


@tasks_bp.route("/<task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id: str) -> Response:
    task = get_services().tasks.get(task_id, get_jwt_identity())
    if task is None:
        return api_response({"message": "Task not found"}, 404)
    return api_response(task, 200)


@tasks_bp.route("/<task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id: str) -> Response:
    updated = get_services().tasks.update(
        task_id, get_jwt_identity(), request.get_json()
    )
    if updated:
        return api_response({"message": "Task updated"}, 200)
    return api_response({"message": "Task not found"}, 404)


@tasks_bp.route("/<task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id: str) -> Response:
    deleted = get_services().tasks.delete(task_id, get_jwt_identity())
    if deleted:
        return api_response({"message": "Task deleted"}, 200)
    return api_response({"message": "Task not found"}, 404)
