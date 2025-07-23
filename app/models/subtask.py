from bson import ObjectId

def subtask_schema():
    return {
        "subtaskId": str(ObjectId()),
        "taskId": str,
        "title": str,
        "done": bool,
        "order": int
    }