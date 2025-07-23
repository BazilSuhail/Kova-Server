from bson import ObjectId
from datetime import datetime

def planner_schema():
    return {
        "plannerId": str(ObjectId()),
        "userId": str,
        "date": str,
        "focusTasks": [str],
        "reflection": str,
        "mood": str  # "happy", "stressed", "focused", etc.
    }