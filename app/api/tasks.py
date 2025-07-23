from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.task_service import create_task, get_tasks, get_task, update_task, delete_task
from ..services.task_service import create_voice_task
from ..utils import api_response

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not "title" in data:
            return api_response({"message": "Title required"}, 400)
        task = create_task(tasks_bp.db, data, user_id)  # Use tasks_bp.db
        print(task)
        return api_response(task, 201)
    except Exception as e:
        return api_response({"message": f"Server error ss: {str(e)}"}, 500)
    
@tasks_bp.route("/create/voice", methods=["POST"])
@jwt_required()
def create_task_route():
    user_id = get_jwt_identity()

    if "file" not in request.files or not request.form.get("title"):
        return api_response({"message": "Audio file and title required."}, 400)

    file = request.files["file"]
    title = request.form["title"]

    try:
        task = create_voice_task(tasks_bp.db, user_id, title, file.stream)
        return api_response(task, 201)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    try:
        user_id = get_jwt_identity()
        tasks = get_tasks(tasks_bp.db, user_id)  # Use tasks_bp.db
        print(tasks)
        return api_response(tasks, 200)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@tasks_bp.route("/<task_id>", methods=["GET"])
@jwt_required()
def get(task_id):
    try:
        user_id = get_jwt_identity()
        task = get_task(tasks_bp.db, task_id, user_id)  # Use tasks_bp.db
        if not task:
            return api_response({"message": "Task not found"}, 404)
        return api_response(task, 200)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@tasks_bp.route("/<task_id>", methods=["PUT"])
@jwt_required()
def update(task_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if update_task(tasks_bp.db, task_id, user_id, data):  # Use tasks_bp.db
            return api_response({"message": "Task updated"}, 200)
        return api_response({"message": "Task not found"}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@tasks_bp.route("/<task_id>", methods=["DELETE"])
@jwt_required()
def delete(task_id):
    try:
        user_id = get_jwt_identity()
        if delete_task(tasks_bp.db, task_id, user_id):  # Use tasks_bp.db
            return api_response({"message": "Task deleted"}, 200)
        return api_response({"message": "Task not found"}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)