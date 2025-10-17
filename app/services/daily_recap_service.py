"""End-of-day recap: today's tasks split by completion, plus the day's planner note.

Replaces the legacy inline route logic, which queried a *local, never
registered* blueprint (``tasks_bp.tasks`` — no such attribute) and built a
tuple from a trailing comma, so the endpoint always returned 500.  The planner
field is ``reflection``: the ``mood`` field it used to read was removed from
the schema (commit 4aa10cc), which is why the legacy code also raised
``KeyError`` once the other bugs were out of the way.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..repositories.planner_repository import PlannerRepository
from ..repositories.task_repository import TaskRepository


class DailyRecapService:
    def __init__(self, tasks: TaskRepository, planners: PlannerRepository) -> None:
        self._tasks = tasks
        self._planners = planners

    def get_recap(self, user_id: str) -> dict[str, Any]:
        """Aggregate today's (UTC) tasks and planner into the recap payload."""
        today = datetime.now(timezone.utc)
        date_prefix = today.strftime("%Y-%m-%d")

        tasks = self._tasks.find_due_on(user_id, date_prefix)
        completed = [task for task in tasks if task.get("isCompleted")]
        pending = [task for task in tasks if not task.get("isCompleted")]

        planner = self._planners.find_by_date(user_id, date_prefix)
        mood = "Not recorded"
        if planner is not None and planner.get("reflection"):
            mood = planner["reflection"]

        return {
            "date": today.isoformat(),
            "completedTasks": [task["title"] for task in completed],
            "pendingTasks": [task["title"] for task in pending],
            "mood": mood,
        }
