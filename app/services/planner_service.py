"""Daily planner: one document per day holding focus items and linked tasks."""
from __future__ import annotations

from typing import Any

from bson import ObjectId

from ..repositories.planner_repository import PlannerRepository
from ..repositories.task_repository import TaskRepository


class PlannerService:
    def __init__(self, planners: PlannerRepository, tasks: TaskRepository) -> None:
        self._planners = planners
        self._tasks = tasks

    def create(self, data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Create a day plan (route already validated ``date`` presence)."""
        document = {
            "plannerId": str(ObjectId()),
            "userId": user_id,
            "date": data["date"],
            "focusTasks": data.get("focusTasks", []),
            "tasks": data.get("tasks", []),
            "reflection": data.get("reflection", ""),
        }
        return self._planners.insert(document)

    def list(self, user_id: str) -> list[dict[str, Any]]:
        """All planners for a user, each enriched with resolved task documents."""
        planners = self._planners.find_for_user(user_id)
        for planner in planners:
            planner["tasksDetails"] = self._tasks.find_many_by_ids(
                planner.get("tasks", [])
            )
        return planners

    def update_focus(self, planner_id: str, user_id: str, focus_tasks: list[Any]) -> bool:
        """Replace the focus list wholesale (the route validated presence)."""
        return (
            self._planners.update_fields(planner_id, user_id, {"focusTasks": focus_tasks})
            > 0
        )

    def update_tasks(self, planner_id: str, user_id: str, task_ids: list[Any]) -> bool:
        """Replace the linked task-id array wholesale."""
        return (
            self._planners.update_fields(planner_id, user_id, {"tasks": task_ids}) > 0
        )

    def delete(self, planner_id: str, user_id: str) -> bool:
        return self._planners.delete(planner_id, user_id) > 0
