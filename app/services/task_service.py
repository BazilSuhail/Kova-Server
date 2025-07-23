from bson import ObjectId
from datetime import datetime
from .. import create_app

app = create_app()
db = app.db

def create_task(data, user_id):
    task = {
        "taskId": str(ObjectId()),
        "userId": user_id,
        "title": data["title"],
        "description": data.get("description", ""),
        "category": data.get("category", ""),
        "dueDate": data.get("dueDate", ""),
        "isCompleted": False,
        "createdFrom": data.get("createdFrom", "manual"),
        "createdAt": datetime.utcnow().isoformat()
    }
    db.tasks.insert_one(task)
    return task

def get_tasks(user_id):
    return list(db.tasks.find({"userId": user_id}))

def get_task(task_id, user_id):
    return db.tasks.find_one({"taskId": task_id, "userId": user_id})

def update_task(task_id, user_id, data):
    update_data = {k: v for k, v in data.items() if k in ["title", "description", "category", "dueDate", "isCompleted"]}
    result = db.tasks.update_one(
        {"taskId": task_id, "userId": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

def delete_task(task_id, user_id):
    result = db.tasks.delete_one({"taskId": task_id, "userId": user_id})
    return result.deleted_count > 0