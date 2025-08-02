from bson import ObjectId

def subtask_schema():
    return {
        "subtaskId": str(ObjectId()),
        "taskId": str,
        "title": str,           # Optional main label/summary
        "done": bool,
        "order": int,
        "subTasks": []          # NEW: array of strings
    }

# from bson import ObjectId

# def subtask_schema():
#     return {
#         "subtaskId": str(ObjectId()),
#         "taskId": str,
#         "title": str,
#         "done": bool,
#         "order": int
#     }