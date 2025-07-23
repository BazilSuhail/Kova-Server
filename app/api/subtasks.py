from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.subtask_service import create_subtask, get_subtasks, update_subtask, delete_subtask
from ..utils import api_response

subtasks_bp = Blueprint("subtasks", __name__)

@subtasks_bp.route("/task/<task_id>", methods=["POST"])
@jwt_required()
def create(task_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not "title" in data:
            return api_response({"message": "Title required"}, 400)
        subtask = create_subtask(data, user_id, task_id)
        return api_response(subtask, 201)
    except ValueError as e:
        return api_response({"message": str(e)}, 404)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@subtasks_bp.route("/task/<task_id>", methods=["GET"])
@jwt_required()
def list_subtasks(task_id):
    try:
        user_id = get_jwt_identity()
        subtasks = get_subtasks(task_id, user_id)
        return api_response(subtasks, 200)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@subtasks_bp.route("/<subtask_id>", methods=["PUT"])
@jwt_required()
def update(subtask_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if update_subtask(subtask_id, user_id, data):
            return api_response({"message": "Subtask updated"}, 200)
        return api_response({"message": "Subtask not found"}, 404)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@subtasks_bp.route("/<subtask_id>", methods=["DELETE"])
@jwt_required()
def delete(subtask_id):
    try:
        user_id = get_jwt_identity()
        if delete_subtask(subtask_id, user_id):
            return api_response({"message": "Subtask deleted"}, 200)
        return api_response({"message": "Subtask not found"}, 404)
    except Exception:
        return api_response({"message": "Server error"}, 500)