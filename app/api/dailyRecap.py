from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime,timezone
from app.utils.api_response import api_response 

daily_recap_bp = Blueprint("daily-recap", __name__)
tasks_bp = Blueprint("tasks", __name__)

@daily_recap_bp.route("/", methods=["GET"])
@jwt_required()
def daily_recap():
    try:
        user_id = get_jwt_identity()
        today_str = datetime.now(timezone.utc).isoformat(), 

        # Fetch today's tasks
        tasks = list(tasks_bp.tasks.find({
            "userId": user_id,
            "dueDate": {"$regex": f"^{today_str}"}
        }))

        completed = [t for t in tasks if t.get("isCompleted")]
        pending = [t for t in tasks if not t.get("isCompleted")]

        # Get planner mood for today
        planner = daily_recap_bp.db.planner.find_one({
            "userId": user_id,
            "date": {"$regex": f"^{today_str}"}
        })
        mood = planner["mood"] if planner else "Not recorded"

        return api_response({
            "date": today_str,
            "completedTasks": [t["title"] for t in completed],
            "pendingTasks": [t["title"] for t in pending],
            "mood": mood
        }, 200)

    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)
