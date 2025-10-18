"""Data access for the ``scheduled_reminders`` collection (feature 10)."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class ReminderRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "scheduled_reminders")

    def find_for_user(
        self, user_id: str, *, status: str | None = None
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"userId": user_id}
        if status is not None:
            query["status"] = status
        return self.find_many(query, sort=("fireAt", 1))

    def find_upcoming(self, user_id: str, from_iso: str) -> list[dict[str, Any]]:
        """Pending reminders due at or after ``from_iso`` (feed/dashboard)."""
        return self.find_many(
            {
                "userId": user_id,
                "status": "pending",
                "fireAt": {"$gte": from_iso},
            },
            sort=("fireAt", 1),
        )

    def find_by_id_for_user(
        self, reminder_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return self.find_one({"reminderId": reminder_id, "userId": user_id})

    def find_due(self, now_iso: str) -> list[dict[str, Any]]:
        """Every pending reminder whose ``fireAt`` has arrived (all users)."""
        return self.find_many(
            {"status": "pending", "fireAt": {"$lte": now_iso}},
            sort=("fireAt", 1),
        )

    def update_fields(self, reminder_id: str, fields: dict[str, Any]) -> int:
        return self.update({"reminderId": reminder_id}, fields).modified_count

    def delete_for_user(self, reminder_id: str, user_id: str) -> int:
        return self.delete_one(
            {"reminderId": reminder_id, "userId": user_id}
        ).deleted_count
