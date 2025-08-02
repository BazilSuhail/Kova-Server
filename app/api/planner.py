from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.planner_service import create_planner, get_planners, update_planner, delete_planner
from app.utils.api_response import api_response

planner_bp = Blueprint("planner", __name__)

@planner_bp.route("/", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not "date" in data:
            return api_response({"message": "Date required"}, 400)
        planner = create_planner(planner_bp.db, data, user_id)
        return api_response(planner, 201)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@planner_bp.route("/", methods=["GET"])
@jwt_required()
def list_planners():
    try:
        user_id = get_jwt_identity()
        planners = get_planners(planner_bp.db, user_id)
        return api_response(planners, 200)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@planner_bp.route("/<planner_id>/focus", methods=["PUT"])
@jwt_required()
def update_focus(planner_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if "focusTasks" not in data:
            return api_response({"message": "focusTasks required"}, 400)
        success = update_focus_tasks(planner_bp.db, planner_id, user_id, data["focusTasks"])
        return api_response({"message": "Focus tasks updated"} if success else {"message": "Planner not found"}, 200 if success else 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@planner_bp.route("/<planner_id>/tasks", methods=["PUT"])
@jwt_required()
def update_tasks(planner_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if "tasks" not in data:
            return api_response({"message": "tasks required"}, 400)
        success = update_tasks_array(planner_bp.db, planner_id, user_id, data["tasks"])
        return api_response({"message": "Task IDs updated"} if success else {"message": "Planner not found"}, 200 if success else 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@planner_bp.route("/<planner_id>", methods=["DELETE"])
@jwt_required()
def delete(planner_id):
    try:
        user_id = get_jwt_identity()
        if delete_planner(planner_bp.db, planner_id, user_id):
            return api_response({"message": "Planner deleted"}, 200)
        return api_response({"message": "Planner not found"}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)


# @planner_bp.route("/", methods=["POST"])
# @jwt_required()
# def create():
#     try:
#         user_id = get_jwt_identity()
#         data = request.get_json()
#         if not data or not "date" in data:
#             return api_response({"message": "Date required"}, 400)
#         planner = create_planner(planner_bp.db, data, user_id)  # Use planner_bp.db
#         return api_response(planner, 201)
#     except Exception as e:
#         return api_response({"message": f"Server error: {str(e)}"}, 500)

# @planner_bp.route("/", methods=["GET"])
# @jwt_required()
# def list_planners():
#     try:
#         user_id = get_jwt_identity()
#         planners = get_planners(planner_bp.db, user_id)  # Use planner_bp.db
#         return api_response(planners, 200)
#     except Exception as e:
#         return api_response({"message": f"Server error: {str(e)}"}, 500)

# @planner_bp.route("/<planner_id>", methods=["PUT"])
# @jwt_required()
# def update(planner_id):
#     try:
#         user_id = get_jwt_identity()
#         data = request.get_json()
#         if update_planner(planner_bp.db, planner_id, user_id, data):  # Use planner_bp.db
#             return api_response({"message": "Planner updated"}, 200)
#         return api_response({"message": "Planner not found"}, 404)
#     except Exception as e:
#         return api_response({"message": f"Server error: {str(e)}"}, 500)

# @planner_bp.route("/<planner_id>", methods=["DELETE"])
# @jwt_required()
# def delete(planner_id):
#     try:
#         user_id = get_jwt_identity()
#         if delete_planner(planner_bp.db, planner_id, user_id):  # Use planner_bp.db
#             return api_response({"message": "Planner deleted"}, 200)
#         return api_response({"message": "Planner not found"}, 404)
#     except Exception as e:
#         return api_response({"message": f"Server error: {str(e)}"}, 500)