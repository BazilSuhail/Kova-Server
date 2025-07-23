from bson import ObjectId

def user_schema():
    return {
        "userId": str(ObjectId()),
        "name": str,
        "email": str,
        "profilePicture": str,
        "preferences": {
            "theme": str,
            "notificationsEnabled": bool
        },
        "createdAt": str
    }