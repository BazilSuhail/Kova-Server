from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify
from .. import create_app

app = create_app()
db = app.db

def get_current_user():
    user_id = get_jwt_identity()
    return db.users.find_one({"userId": user_id}, {"password": 0})