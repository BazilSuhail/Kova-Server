"""Subtask generation/listing tied to a parent task.

Subtasks are created as one document holding an LLM-generated ``subTasks``
array — the API never creates individual subtask rows.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from ..core.exceptions import AIProviderError, NotFoundError
from ..repositories.subtask_repository import SubtaskRepository
from ..repositories.task_repository import TaskRepository
from ..utils.sub_tasks_utils import generate_subtasks_from_description

logger = logging.getLogger(__name__)

# Whitelist for partial updates.
_UPDATABLE_FIELDS = ("title", "done", "order")


class SubtaskService:
    def __init__(
        self,
        subtasks: SubtaskRepository,
        tasks: TaskRepository,
        tombstones: object | None = None,
    ) -> None:
        self._subtasks = subtasks
        self._tasks = tasks
        self._tombstones = tombstones

    def create(self, data: dict[str, Any], user_id: str, task_id: str) -> dict[str, Any]:
        """Generate subtasks for an owned task from its description."""
        task = self._tasks.find_for_user(task_id, user_id)
        if task is None:
            raise NotFoundError("Task not found")
        if not task.get("hasSubtasks", False):
            self._tasks.set_has_subtasks(task_id, True)
        try:
            subtask_lines = generate_subtasks_from_description(
                task.get("description", "")
            )
        except ValueError as exc:
            # Tracked fix (docs/TODO.md): an LLM/transport failure is an
            # upstream problem, not "task not found" — the legacy route mapped
            # every ValueError to 404. Missing tasks still 404 above; a missing
            # API key surfaces from the generator as AIConfigError → 503.
            logger.exception(
                "subtask_generation_failed", extra={"task_id": task_id}
            )
            raise AIProviderError("Subtask generation failed") from exc
        document = {
            "subtaskId": str(ObjectId()),
            "taskId": task_id,
            "title": data.get("title", "Generated subtasks"),
            "done": False,
            "order": data.get("order", 1),
            "subTasks": subtask_lines,
        }
        return self._subtasks.insert(document)

    def list(self, task_id: str, user_id: str) -> list[dict[str, Any]]:
        """List a task's subtasks, shaped exactly like the legacy response."""
        if self._tasks.find_for_user(task_id, user_id) is None:
            raise NotFoundError("Task not found")
        return [
            {
                "subtaskId": subtask["subtaskId"],
                "title": subtask.get("title", ""),
                "order": subtask.get("order", 1),
                "done": subtask.get("done", False),
                "subTasks": subtask.get("subTasks", []),
            }
            for subtask in self._subtasks.find_by_task(task_id)
        ]

    def update(self, subtask_id: str, user_id: str, data: dict[str, Any]) -> bool:
        """Partial update; ownership is proven through the parent task."""
        subtask = self._subtasks.find_by_subtask_id(subtask_id)
        if subtask is None:
            return False
        if self._tasks.find_for_user(subtask["taskId"], user_id) is None:
            return False
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        return self._subtasks.update_fields(subtask_id, fields) > 0

    def delete_for_task(self, task_id: str, user_id: str) -> int:
        """Delete *all* subtasks of an owned task; returns how many went away."""
        if self._tasks.find_for_user(task_id, user_id) is None:
            raise NotFoundError("Task not found")
        removed_ids = [
            subtask["subtaskId"] for subtask in self._subtasks.find_by_task(task_id)
        ]
        deleted = self._subtasks.delete_by_task(task_id)
        self._tasks.set_has_subtasks(task_id, False)
        if self._tombstones is not None:
            for subtask_id in removed_ids:
                self._tombstones.record(  # type: ignore[attr-defined]
                    user_id, "subtasks", subtask_id, datetime.now(UTC).isoformat()
                )
        return deleted

    def delete_one(self, subtask_id: str, user_id: str) -> bool:
        """Delete a single subtask; ownership is proven through the parent task.

        When the last subtask of a task goes away, the parent's
        ``hasSubtasks`` flag is reset to ``False``.
        """
        subtask = self._subtasks.find_by_subtask_id(subtask_id)
        if subtask is None:
            return False
        if self._tasks.find_for_user(subtask["taskId"], user_id) is None:
            return False
        if self._subtasks.delete_by_subtask_id(subtask_id) == 0:
            return False
        if not self._subtasks.find_by_task(subtask["taskId"]):
            self._tasks.set_has_subtasks(subtask["taskId"], False)
        if self._tombstones is not None:
            self._tombstones.record(  # type: ignore[attr-defined]
                user_id, "subtasks", subtask_id, datetime.now(UTC).isoformat()
            )
        return True
