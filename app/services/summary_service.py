from bson import ObjectId
from datetime import datetime, timezone 
from app.utils.summary_utils import generate_summary_from_llm

def create_summary(db, user_id, extracted_text, original_filename):
    # Feed text to LLM
    summary_bullets = generate_summary_from_llm(extracted_text)

    # Create task object (you can set proper values later from another process)
    task = {
        "taskId": str(ObjectId()),
        "userId": user_id,
        "title": "Summary Task",
        "description": " ".join(summary_bullets),  # or pick summary_bullets[0] as main point
        "category": "Uncategorized",
        "dueDate": "",
        "isCompleted": False,
        "createdFrom": "natural-language",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Create summary
    summary = {
        "summaryId": str(ObjectId()),
        "userId": user_id,
        "sourceType": "pdf",
        "originalFileName": original_filename,
        "summaryBullets": summary_bullets,
        "createdAt": datetime.utcnow().isoformat()
    }

    db.summaries.insert_one(summary)

    return {
        "summary": summary,
        "task": task
    }

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