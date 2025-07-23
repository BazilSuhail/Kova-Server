from bson import ObjectId
from .. import create_app

app = create_app()
db = app.db

def create_subtask(data, user_id, task_id):
    if not db.tasks.find_one({"taskId": task_id, "userId": user_id}):
        raise ValueError("Task not found")
    subtask = {
        "subtaskId": str(ObjectId()),
        "taskId": task_id,
        "title": data["title"],
        "done": False,
        "order": data.get("order", 1)
    }
    db.subtasks.insert_one(subtask)
    return subtask

def get_subtasks(task_id, user_id):
    return list(db.subtasks.find({"taskId": task_id}))

def update_subtask(subtask_id, user_id, data):
    subtask = db.subtasks.find_one({"subtaskId": subtask_id})
    if not subtask or not db.tasks.find_one({"taskId": subtask["taskId"], "userId": user_id}):
        return False
    update_data = {k: v for k, v in data.items() if k in ["title", "done", "order"]}
    result = db.subtasks.update_one({"subtaskId": subtask_id}, {"$set": update_data})
    return result.modified_count > 0

def delete_subtask(subtask_id, user_id):
    subtask = db.subtasks.find_one({"subtaskId": subtask_id})
    if not subtask or not db.tasks.find_one({"taskId": subtask["taskId"], "userId": user_id}):
        return False
    result = db.subtasks.delete_one({"subtaskId": subtask_id})
    return result.deleted_count > 0