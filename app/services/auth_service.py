from bson import ObjectId
from datetime import datetime
import bcrypt

def signup_user(db, data):
    print(f"Inside signup_user, db: {db}, data: {data}")  # Debug
    if db.users.find_one({"email": data["email"]}):
        raise ValueError("Email already exists")
    print("sd")  # Debug
    hashed_password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = {
        "userId": str(ObjectId()),
        "name": data["name"],
        "email": data["email"],
        "password": hashed_password,
        "profilePicture": data.get("profilePicture", ""),
        "preferences": data.get("preferences", {"theme": "light", "notificationsEnabled": True}),
        "createdAt": datetime.utcnow().isoformat()
    }
    db.users.insert_one(user)
    return user

def login_user(db, email, password):
    print(f"Inside login_user, db: {db}, email: {email}")  # Debug
    user = db.users.find_one({"email": email})
    if not user:
        raise ValueError("User not found")
    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        raise ValueError("Invalid password")
    return user