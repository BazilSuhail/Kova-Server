from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token
from ..services.user_service import create_user, get_user

users_bp = Blueprint("users", __name__)

@users_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    user = create_user(data)
    return jsonify({"message": "User created", "userId": user["userId"]}), 201

@users_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = get_user(data["email"])
    if user and data["password"] == "password":  # Replace with secure password check
        access_token = create_access_token(identity=user["userId"])
        return jsonify({"access_token": access_token}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    return jsonify(user), 200