from flask import Blueprint, jsonify, request

users_bp = Blueprint('users', __name__)

users = [
    {'id': 1, 'name': 'Alice'},
    {'id': 2, 'name': 'Booba'}
]

@users_bp.route('/', methods=['GET'])
def get_users():
    return jsonify(users)

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404

@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = {
        'id': len(users) + 1,
        'name': data.get('name')
    }
    users.append(new_user)
    return jsonify(new_user), 201
