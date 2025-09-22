from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..services.auth_service import signup_user, login_user
from app.utils.api_response import api_response

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        print(f"Received signup data: {data}")  # Debug
        if not data or not all(key in data for key in ["name", "email", "password"]):
            return api_response({"message": "Missing required fields"}, 400)
        print(f"Attempting to access db: {auth_bp.db}")  # Debug
        user = signup_user(auth_bp.db, data)  # Use auth_bp.db
        print(f"User created: {user}")  # Debug
        access_token = create_access_token(identity=user["userId"])
        return api_response({"message": "User created", "access_token": access_token, "userId": user["userId"]}, 201)
    except ValueError as e:
        print(f"Signup ValueError: {e}")  # Debug
        return api_response({"message": str(e)}, 400)
    except Exception as e:
        print(f"Signup Exception: {str(e)}")  # Debug
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        
        if not data or not all(key in data for key in ["email", "password"]):
            return api_response({"message": "Missing required fields"}, 400)
        
        user = login_user(auth_bp.db, data["email"], data["password"])  # Use auth_bp.db
        print(f"User logged in: {user}")  # Debug
        access_token = create_access_token(identity=user["userId"])
        return api_response({"access_token": access_token, "userId": user["userId"]}, 200)
    except ValueError as e:
        print(f"Login ValueError: {e}")  # Debug
        return api_response({"message": str(e)}, 401)
    except Exception as e:
        print(f"Login Exception: {str(e)}")  # Debug
        return api_response({"message": f"Server error: {str(e)}"}, 500)