from bson import ObjectId
from datetime import datetime

def create_task(db, data, user_id):
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

def get_tasks(db, user_id):
    return list(db.tasks.find({"userId": user_id}))

def get_task(db, task_id, user_id):
    return db.tasks.find_one({"taskId": task_id, "userId": user_id})

def update_task(db, task_id, user_id, data):
    print(task_id,user_id,"----")
    update_data = {k: v for k, v in data.items() if k in ["title", "description", "category", "dueDate", "isCompleted"]}
    task = db.tasks.find_one({"taskId": task_id, "userId": user_id})
    print(task)  # Should show the document if it exists
    result = db.tasks.update_one(
        {"taskId": task_id, "userId": user_id},
        {"$set": update_data}
    )
    print(result)

    return result.modified_count > 0

def delete_task(db, task_id, user_id):
    result = db.tasks.delete_one({"taskId": task_id, "userId": user_id})
    return result.deleted_count > 0