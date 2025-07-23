from bson import ObjectId
from datetime import datetime

def create_planner(db, data, user_id):
    planner = {
        "plannerId": str(ObjectId()),
        "userId": user_id,
        "date": data["date"],
        "focusTasks": data.get("focusTasks", []),
        "reflection": data.get("reflection", ""),
        "mood": data.get("mood", "")
    }
    db.planner.insert_one(planner)
    return planner

def get_planners(db, user_id):
    return list(db.planner.find({"userId": user_id}))

def update_planner(db, planner_id, user_id, data):
    update_data = {k: v for k, v in data.items() if k in ["date", "focusTasks", "reflection", "mood"]}
    result = db.planner.update_one(
        {"plannerId": planner_id, "userId": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

def delete_planner(db, planner_id, user_id):
    result = db.planner.delete_one({"plannerId": planner_id, "userId": user_id})
    return result.deleted_count > 0