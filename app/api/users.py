from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.user_service import get_user_by_id, update_user, delete_user
from ..utils import api_response

users_bp = Blueprint("users", __name__)

@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = get_user_by_id(users_bp.db, user_id)  # Use users_bp.db
        return api_response(user, 200)
    except ValueError as e:
        return api_response({"message": str(e)}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@users_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        updated_user = update_user(users_bp.db, user_id, data)  # Use users_bp.db
        return api_response(updated_user, 200)
    except ValueError as e:
        return api_response({"message": str(e)}, 400)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@users_bp.route("/profile", methods=["DELETE"])
@jwt_required()
def delete_profile():
    try:
        user_id = get_jwt_identity()
        delete_user(users_bp.db, user_id)  # Use users_bp.db
        return api_response({"message": "User deleted"}, 200)
    except ValueError as e:
        return api_response({"message": str(e)}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)