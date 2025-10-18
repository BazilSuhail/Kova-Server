"""Data access for the ``mood_entries`` collection (features 6 & 12)."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class MoodRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "mood_entries")

    def find_for_user(
        self, user_id: str, *, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Newest-first mood log; ``limit`` caps the feed length."""
        rows = self.find_many({"userId": user_id}, sort=("loggedAt", -1))
        return rows[:limit] if limit else rows

    def find_since(self, user_id: str, since: str | None) -> list[dict[str, Any]]:
        return self.find_updated_since(user_id, since)

    def find_by_id_for_user(
        self, mood_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return self.find_one({"moodId": mood_id, "userId": user_id})

    def find_in_window(
        self, user_id: str, start_prefix: str, end_prefix: str
    ) -> list[dict[str, Any]]:
        """Entries logged within ``[start_prefix, end_prefix)`` (ISO strings)."""
        return self.find_many(
            {
                "userId": user_id,
                "loggedAt": {"$gte": start_prefix, "$lt": end_prefix},
            },
            sort=("loggedAt", 1),
        )

    def update_fields(self, mood_id: str, user_id: str, fields: dict[str, Any]) -> int:
        return self.update({"moodId": mood_id, "userId": user_id}, fields).modified_count

    def delete_for_user(self, mood_id: str, user_id: str) -> int:
        return self.delete_one(
            {"moodId": mood_id, "userId": user_id}
        ).deleted_count
