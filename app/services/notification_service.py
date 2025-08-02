from bson import ObjectId
from datetime import datetime, timezone

def create_notification(db, user_id, data):
    notification = {
        "notificationId": str(ObjectId()),
        "userId": user_id,
        "title": data["title"],
        "message": data["message"],
        "type": data.get("type", ""),         # optional
        "relatedId": data.get("relatedId", ""),  # optional
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "triggerTime": data.get("triggerTime")  # optional ISO date
    }
    db.notifications.insert_one(notification)
    return notification

def get_notifications(db, user_id):
    return list(db.notifications.find({"userId": user_id}).sort("createdAt", -1))

def update_notification(db, notification_id, user_id, data):
    allowed_fields = ["read", "title", "message", "triggerTime"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    result = db.notifications.update_one(
        {"notificationId": notification_id, "userId": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0
