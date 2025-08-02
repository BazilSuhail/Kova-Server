from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.subtask_service import create_subtask, get_subtasks, update_subtask, delete_subtasks
from app.utils.api_response import api_response

subtasks_bp = Blueprint("subtasks", __name__)

@subtasks_bp.route("/create", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or "taskId" not in data:
            return api_response({"message": "taskId is required"}, 400)

        task_id = data["taskId"]
        subtask = create_subtask(subtasks_bp.db, data, user_id, task_id)
        return api_response(subtask, 201)

    except ValueError as e:
        return api_response({"message": str(e)}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

# curl -X GET http://localhost:5000/api/subtasks/task/688e16eca8fa7c7a2adf0c55 -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc1NDE0MTA1MiwianRpIjoiNDUwZmQ0MjMtNTEyNi00ZjMzLThjYWMtNTc2OTI2MDBmZmIxIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjY4ODYyZTU5ZWQ5MjkzYjBhZDE3YjI3ZiIsIm5iZiI6MTc1NDE0MTA1MiwiY3NyZiI6ImFhMzIwNWE4LWY2YTYtNGNlNC1iZmE1LTQ3ZGRjMDBhNDM3MCIsImV4cCI6MTc1NDE0NDY1Mn0.7YBiaLsUlj7g2keRuUiG19kVHSe37NDkNrJZK6j1BCw"
@subtasks_bp.route("/task/<task_id>", methods=["GET"])
@jwt_required()
def list_subtasks(task_id):
    try:
        user_id = get_jwt_identity()
        subtasks = get_subtasks(subtasks_bp.db, task_id, user_id)
        return api_response(subtasks, 200)
    except ValueError as e:
        return api_response({"message": str(e)}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)


@subtasks_bp.route("/<subtask_id>", methods=["PUT"])
@jwt_required()
def update(subtask_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if update_subtask(subtasks_bp.db, subtask_id, user_id, data):  # Use subtasks_bp.db
            return api_response({"message": "Subtask updated"}, 200)
        return api_response({"message": "Subtask not found"}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@subtasks_bp.route("/task/<task_id>", methods=["DELETE"])
@jwt_required()
def delete_subtasks_for_task(task_id):
    try:
        user_id = get_jwt_identity()

        task = subtasks_bp.db.tasks.find_one({"taskId": task_id, "userId": user_id})
        if not task:
            return api_response({"message": "Task not found"}, 404)

        deleted_count = delete_subtasks(subtasks_bp.db, task_id)

        return api_response({
            "message": f"{deleted_count} subtask(s) deleted for taskId {task_id}"
        }, 200)

    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)
