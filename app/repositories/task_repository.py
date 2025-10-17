"""Data access for the ``tasks`` collection."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class TaskRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "tasks")

    def find_all(self, user_id: str) -> list[dict[str, Any]]:
        return self.find_many({"userId": user_id})

    def find_for_user(self, task_id: str, user_id: str) -> dict[str, Any] | None:
        """Ownership check: every task read is scoped to its owner."""
        return self.find_one({"taskId": task_id, "userId": user_id})

    def find_by_id(self, task_id: str) -> dict[str, Any] | None:
        """Owner-agnostic lookup (subtask ownership is verified separately)."""
        return self.find_one({"taskId": task_id})

    def find_many_by_ids(self, task_ids: list[str]) -> list[dict[str, Any]]:
        """Resolve a planner's task-id array into full task documents."""
        return self.find_many({"taskId": {"$in": task_ids}})

    def find_due_on(self, user_id: str, date_prefix: str) -> list[dict[str, Any]]:
        """Tasks due on a day.

        ``dueDate`` is free-form text: clients send ``YYYY-MM-DD`` or a full
        ISO timestamp, so a prefix match covers both.
        """
        return self.find_many({"userId": user_id, "dueDate": {"$regex": f"^{date_prefix}"}})

    def insert_task(self, document: dict[str, Any]) -> dict[str, Any]:
        return self.insert(document)

    def update_fields(self, task_id: str, user_id: str, fields: dict[str, Any]) -> int:
        return self.update({"taskId": task_id, "userId": user_id}, fields).modified_count

    def delete(self, task_id: str, user_id: str) -> int:
        return self.delete_one({"taskId": task_id, "userId": user_id}).deleted_count

    def set_has_subtasks(self, task_id: str, value: bool) -> None:
        """Flip the parent's ``hasSubtasks`` flag (no owner check — callers did it)."""
        self.update({"taskId": task_id}, {"hasSubtasks": value})
