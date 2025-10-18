"""Daily planner: one document per day holding focus items and linked tasks."""
from __future__ import annotations

import builtins
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from ..core.exceptions import ValidationError
from ..repositories.planner_repository import PlannerRepository
from ..repositories.task_repository import TaskRepository

# Fields a client may change through PUT /api/planner/<id> (id/owner immutable).
_UPDATABLE_FIELDS = ("date", "focusTasks", "tasks", "reflection")


class PlannerService:
    def __init__(
        self,
        planners: PlannerRepository,
        tasks: TaskRepository,
        tombstones: object | None = None,
    ) -> None:
        self._planners = planners
        self._tasks = tasks
        self._tombstones = tombstones

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
        # One $in lookup for every planner instead of one query per planner
        # (the legacy loop was an N+1). Output order still follows each
        # planner's own `tasks` array; dangling ids are dropped, as before.
        wanted = {
            task_id for planner in planners for task_id in planner.get("tasks", [])
        }
        tasks_by_id = {
            task["taskId"]: task
            for task in (self._tasks.find_many_by_ids(sorted(wanted)) if wanted else [])
        }
        for planner in planners:
            planner["tasksDetails"] = [
                tasks_by_id[task_id]
                for task_id in dict.fromkeys(planner.get("tasks", []))
                if task_id in tasks_by_id
            ]
        return planners

    def update_focus(
        self, planner_id: str, user_id: str, focus_tasks: builtins.list[Any]
    ) -> bool:
        """Replace the focus list wholesale (the route validated presence)."""
        return (
            self._planners.update_fields(planner_id, user_id, {"focusTasks": focus_tasks})
            > 0
        )

    def update_tasks(
        self, planner_id: str, user_id: str, task_ids: builtins.list[Any]
    ) -> bool:
        """Replace the linked task-id array wholesale."""
        return (
            self._planners.update_fields(planner_id, user_id, {"tasks": task_ids}) > 0
        )

    def update(
        self, planner_id: str, user_id: str, data: dict[str, Any]
    ) -> bool:
        """Apply whitelisted changes; False = no such planner (owner-scoped).

        Unlike the legacy partial-update routes, an *existing* planner that
        receives identical values still counts as updated — only a missing
        document yields 404.
        """
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        if not fields:
            raise ValidationError(
                "No updatable fields; expected one of: "
                + ", ".join(_UPDATABLE_FIELDS)
            )
        if self._planners.find_by_id_for_user(planner_id, user_id) is None:
            return False
        self._planners.update_fields(planner_id, user_id, fields)
        return True

    def delete(self, planner_id: str, user_id: str) -> bool:
        deleted = self._planners.delete(planner_id, user_id) > 0
        if deleted and self._tombstones is not None:
            self._tombstones.record(  # type: ignore[attr-defined]
                user_id, "planner", planner_id, datetime.now(UTC).isoformat()
            )
        return deleted
