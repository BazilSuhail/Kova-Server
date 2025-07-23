from bson import ObjectId
from datetime import datetime

def user_schema():
    return {
        "userId": str(ObjectId()),
        "name": str,
        "email": str,
        "password": str,
        "profilePicture": str,
        "preferences": {
            "theme": str,
            "notificationsEnabled": bool
        },
        "createdAt": str
    }