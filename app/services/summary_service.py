from bson import ObjectId
from datetime import datetime

def create_summary(db, data, user_id):
    summary = {
        "summaryId": str(ObjectId()),
        "userId": user_id,
        "sourceType": data["sourceType"],
        "originalFileName": data.get("originalFileName", ""),
        "summaryBullets": data.get("summaryBullets", []),
        "createdAt": datetime.utcnow().isoformat()
    }
    db.summaries.insert_one(summary)
    return summary

def get_summaries(db, user_id):
    return list(db.summaries.find({"userId": user_id}))

def update_summary(db, summary_id, user_id, data):
    update_data = {k: v for k, v in data.items() if k in ["sourceType", "originalFileName", "summaryBullets"]}
    result = db.summaries.update_one(
        {"summaryId": summary_id, "userId": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

def delete_summary(db, summary_id, user_id):
    result = db.summaries.delete_one({"summaryId": summary_id, "userId": user_id})
    return result.deleted_count > 0