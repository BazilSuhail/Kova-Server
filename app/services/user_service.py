from bson import ObjectId
from .. import create_app

app = create_app()
db = app.db

def create_user(data):
    user = {
        "userId": str(ObjectId()),
        "name": data["name"],
        "email": data["email"],
        "profilePicture": data.get("profilePicture", ""),
        "preferences": data.get("preferences", {"theme": "light", "notificationsEnabled": True}),
        "createdAt": data.get("createdAt", datetime.utcnow().isoformat())
    }
    db.users.insert_one(user)
    return user

def get_user(email):
    return db.users.find_one({"email": email})

def get_user_by_id(user_id):
    return db.users.find_one({"userId": user_id})