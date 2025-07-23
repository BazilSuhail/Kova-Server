from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..services.auth_service import signup_user, login_user
from ..utils import api_response

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ["name", "email", "password"]):
            return api_response({"message": "Missing required fields"}, 400)
        user = signup_user(data)
        access_token = create_access_token(identity=user["userId"])
        return api_response({"message": "User created", "access_token": access_token, "userId": user["userId"]}, 201)
    except ValueError as e:
        return api_response({"message": str(e)}, 400)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ["email", "password"]):
            return api_response({"message": "Missing required fields"}, 400)
        user = login_user(data["email"], data["password"])
        access_token = create_access_token(identity=user["userId"])
        return api_response({"access_token": access_token, "userId": user["userId"]}, 200)
    except ValueError as e:
        return api_response({"message": str(e)}, 401)
    except Exception:
        return api_response({"message": "Server error"}, 500)