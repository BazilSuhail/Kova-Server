from bson import ObjectId

def get_user_by_id(db, user_id):
    user = db.users.find_one({"userId": user_id}, {"password": 0})
    if not user:
        raise ValueError("User not found")
    return user

def update_user(db, user_id, data):
    update_data = {k: v for k, v in data.items() if k in ["name", "email", "profilePicture", "preferences"]}
    if "email" in update_data and db.users.find_one({"email": update_data["email"], "userId": {"$ne": user_id}}):
        raise ValueError("Email already in use")
    result = db.users.update_one({"userId": user_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise ValueError("User not found or no changes made")
    return get_user_by_id(db, user_id)

def delete_user(db, user_id):
    result = db.users.delete_one({"userId": user_id})
    if result.deleted_count == 0:
        raise ValueError("User not found")
    return True