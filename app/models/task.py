from bson import ObjectId

def task_schema():
    return {
        "taskId": str(ObjectId()),
        "userId": str,
        "title": str,
        "description": str,
        "category": str,
        "dueDate": str,
        "isCompleted": bool,
        "createdFrom": str,  # "voice", "nlp", "ocr", "manual"
        "createdAt": str
    }