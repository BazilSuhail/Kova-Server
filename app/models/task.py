from bson import ObjectId
from datetime import datetime

def task_schema(data=None):
    data = data or {}
    return {
        "taskId": str(ObjectId()),
        "userId": data.get("userId", ""),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "category": data.get("category", ""),
        "dueDate": data.get("dueDate", ""),
        "isCompleted": data.get("isCompleted", False),
        "createdFrom": data.get("createdFrom", "manual"),  # default to manual
        "createdAt": datetime.utcnow().isoformat(),
        "subtasks": data.get("subtasks", [])  # default: empty list
    }
