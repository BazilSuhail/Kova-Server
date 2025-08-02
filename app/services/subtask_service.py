from bson import ObjectId
from app.utils.sub_tasks_utils import make_subTasks_from_tasks_description

def create_subtask(db, data, user_id, task_id):
    task = db.tasks.find_one({"taskId": task_id, "userId": user_id})
    if not task:
        raise ValueError("Task not found")

    # Mark the task as having subtasks if not already
    if not task.get("hasSubtasks", False):
        db.tasks.update_one({"taskId": task_id}, {"$set": {"hasSubtasks": True}})

    # Extract subtask strings from task description
    description = task.get("description", "")
    subtask_lines = make_subTasks_from_tasks_description(description)

    # Create a single subtask document with subTasks array
    subtask_doc = {
        "subtaskId": str(ObjectId()),
        "taskId": task_id,
        "title": data.get("title", "Generated subtasks"),
        "done": False,
        "order": data.get("order", 1),
        "subTasks": subtask_lines
    }

    db.subtasks.insert_one(subtask_doc)
    return subtask_doc



def get_subtasks(db, task_id, user_id):
    return list(db.subtasks.find({"taskId": task_id}))

def update_subtask(db, subtask_id, user_id, data):
    subtask = db.subtasks.find_one({"subtaskId": subtask_id})
    if not subtask or not db.tasks.find_one({"taskId": subtask["taskId"], "userId": user_id}):
        return False
    update_data = {k: v for k, v in data.items() if k in ["title", "done", "order"]}
    result = db.subtasks.update_one({"subtaskId": subtask_id}, {"$set": update_data})
    return result.modified_count > 0

def delete_subtask(db, subtask_id, user_id):
    subtask = db.subtasks.find_one({"subtaskId": subtask_id})
    if not subtask or not db.tasks.find_one({"taskId": subtask["taskId"], "userId": user_id}):
        return False
    result = db.subtasks.delete_one({"subtaskId": subtask_id})
    return result.deleted_count > 0