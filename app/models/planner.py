from bson import ObjectId
from datetime import datetime, timezone

def planner_schema():
    return {
        "plannerId": str(ObjectId()),
        "userId": str,
        "date": datetime.now(timezone.utc).isoformat(),  # ISO timestamp
        "focusTasks": [],    # List of focus task titles or IDs (your choice)
        "tasks": [],         # ✅ General task titles or IDs
        "reflection": "", 
    }
