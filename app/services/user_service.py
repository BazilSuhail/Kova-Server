from bson import ObjectId
from .. import create_app

app = create_app()
db = app.db

def get_user_by_id(user_id):
    user = db.users.find_one({"userId": user_id}, {"password": 0})
    if not user:
        raise ValueError("User not found")
    return user

def update_user(user_id, data):
    allowed_fields = ["name", "email", "profilePicture", "preferences"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if "email" in update_data:
        existing = db.users.find_one({"email": update_data["email"], "userId": {"$ne": user_id}})
        if existing:
            raise ValueError("Email already in use")

    result = db.users.update_one({"userId": user_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise ValueError("User not found or no changes made")
    return get_user_by_id(user_id)

def delete_user(user_id):
    result = db.users.delete_one({"userId": user_id})
    if result.deleted_count == 0:
        raise ValueError("User not found")
    return {"message": "User deleted"}, 200
