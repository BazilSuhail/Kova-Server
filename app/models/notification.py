from bson import ObjectId
from datetime import datetime, timezone

def notification_schema():
    return {
        "notificationId": str(ObjectId()),
        "userId": str,
        "title": str,                  # e.g., "Task due soon"
        "message": str,                # e.g., "Finish your task: 'Submit report'"
        "type": str,                   # "task", "subtask", "planner"
        "relatedId": str,              # taskId, subtaskId, or plannerId
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "triggerTime": None            # ISO datetime string for scheduled ones
    }
