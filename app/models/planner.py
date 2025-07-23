from bson import ObjectId

def planner_schema():
    return {
        "plannerId": str(ObjectId()),
        "userId": str,
        "date": str,
        "focusTasks": [str],
        "reflection": str,
        "mood": str  # "happy", "stressed", "focused", etc.
    }