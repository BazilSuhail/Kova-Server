from bson import ObjectId
from datetime import datetime
from .. import create_app

app = create_app()
db = app.db

def create_notification(data, user_id):
    notification = {
        "notificationId": str(ObjectId()),
        "userId": user_id,
        "title": data["title"],
        "message": data["message"],
        "read": False,
        "type": data.get("type", "reminder"),
        "createdAt": datetime.utcnow().isoformat()
    }
    db.notifications.insert_one(notification)
    return notification

def get_notifications(user_id):
    return list(db.notifications.find({"userId": user_id}))

def update_notification(notification_id, user_id, data):
    update_data = {k: v for k, v in data.items() if k in ["read"]}
    result = db.notifications.update_one(
        {"notificationId": notification_id, "userId": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

def delete_notification(notification_id, user_id):
    result = db.notifications.delete_one({"notificationId": notification_id, "userId": user_id})
    return result.deleted_count > 0