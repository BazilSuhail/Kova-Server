from bson import ObjectId 

def create_planner(db, data, user_id):
    planner = {
        "plannerId": str(ObjectId()),
        "userId": user_id,
        "date": data["date"],
        "focusTasks": data.get("focusTasks", []),
        "tasks": data.get("tasks", []),  # Default empty if not provided
        "reflection": data.get("reflection", ""), 
    }
    db.planner.insert_one(planner)
    return planner

def get_planners(db, user_id):
    planners = list(db.planner.find({"userId": user_id}))
    for planner in planners:
        task_ids = planner.get("tasks", [])
        tasks = list(db.tasks.find({"taskId": {"$in": task_ids}}))
        planner["tasksDetails"] = tasks
    return planners

def update_focus_tasks(db, planner_id, user_id, focus_tasks):
    result = db.planner.update_one(
        {"plannerId": planner_id, "userId": user_id},
        {"$set": {"focusTasks": focus_tasks}}
    )
    return result.modified_count > 0

def update_tasks_array(db, planner_id, user_id, tasks):
    result = db.planner.update_one(
        {"plannerId": planner_id, "userId": user_id},
        {"$set": {"tasks": tasks}}
    )
    return result.modified_count > 0

def delete_planner(db, planner_id, user_id):
    result = db.planner.delete_one({"plannerId": planner_id, "userId": user_id})
    return result.deleted_count > 0
