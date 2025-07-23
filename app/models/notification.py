from bson import ObjectId
from datetime import datetime

def notification_schema():
    return {
        "notificationId": str(ObjectId()),
        "userId": str,
        "title": str,
        "message": str,
        "read": bool,
        "type": str,  # "reminder", "system", "planner", "task"
        "createdAt": str
    }