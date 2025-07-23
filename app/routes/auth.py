from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models.user import get_user_by_username, create_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if get_user_by_username(data['username']):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = generate_password_hash(data['password'])
    create_user({"username": data['username'], "password": hashed_pw})
    return jsonify({"message": "User created"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = get_user_by_username(data['username'])
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user['_id']))
    return jsonify({"token": token}), 200
