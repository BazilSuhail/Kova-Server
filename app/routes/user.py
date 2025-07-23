from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.schemas.user_schema import UserSchema
from app.extensions import mongo
from datetime import datetime

user_bp = Blueprint('users', __name__)

@user_bp.route('/', methods=['POST'])
def create_user():
    json_data = request.get_json()

    try:
        # Validate input
        data = UserSchema().load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    # Add createdAt if missing
    if "createdAt" not in data:
        data["createdAt"] = datetime.utcnow()

    mongo.db.users.insert_one(data)
    return jsonify({"message": "User created", "user": data}), 201
