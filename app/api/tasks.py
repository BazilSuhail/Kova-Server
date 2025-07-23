from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.task_service import create_task, get_tasks, get_task, update_task, delete_task, create_voice_task, create_nlp_task
from app.utils.api_response import api_response

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not "title" in data:
            return api_response({"message": "Title required"}, 400)
        task = create_task(tasks_bp.db, data, user_id)
        print(task)
        return api_response(task, 201)
    except Exception as e:
        return api_response({"message": f"Server error ss: {str(e)}"}, 500)
    
@tasks_bp.route("/create/natural-language", methods=["POST"])
@jwt_required()
def create_task_from_natural_language():
    user_id = get_jwt_identity()
    if not request.is_json:
        return api_response({"message": "Request must be JSON"}, 415)

    data = request.get_json()
    
    if not data or "prompt" not in data:
        return api_response({"message": "prompt is required in JSON body"},400)

    try: 
        task = create_nlp_task(db=tasks_bp.db,user_id=user_id,prompt=data["prompt"])        
        return api_response(task, 201)
    
    except ValueError as e:
        return api_response({"message": str(e)}, 400)
    except Exception as e: 
        return api_response({"message": "Internal server error"}, 500)
    
@tasks_bp.route("/create/voice", methods=["POST"])
@jwt_required()
def create_task_from_voice():
    user_id = get_jwt_identity()

    if "file" not in request.files:
        return api_response({"message": "Audio file is required."}, 400)

    file = request.files["file"]

    try:
        task = create_voice_task(tasks_bp.db, user_id, file.stream)
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