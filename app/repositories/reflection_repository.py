"""Data access for the ``reflections`` collection (feature 18 — journal)."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class ReflectionRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "reflections")

    def find_for_user(
        self, user_id: str, *, limit: int | None = None
    ) -> list[dict[str, Any]]:
        rows = self.find_many({"userId": user_id}, sort=("date", -1))
        return rows[:limit] if limit else rows

    def find_since(self, user_id: str, since: str | None) -> list[dict[str, Any]]:
        return self.find_updated_since(user_id, since)

    def find_by_date(self, user_id: str, date: str) -> dict[str, Any] | None:
        """Entries store ``date`` as ``YYYY-MM-DD`` (prefix match tolerates ISO)."""
        return self.find_one(
            {"userId": user_id, "date": {"$regex": f"^{date}"}}
        )

    def find_by_id_for_user(
        self, reflection_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return self.find_one(
            {"reflectionId": reflection_id, "userId": user_id}
        )

    def update_fields(
        self, reflection_id: str, user_id: str, fields: dict[str, Any]
    ) -> int:
        return self.update(
            {"reflectionId": reflection_id, "userId": user_id}, fields
        ).modified_count

    def delete_for_user(self, reflection_id: str, user_id: str) -> int:
        return self.delete_one(
            {"reflectionId": reflection_id, "userId": user_id}
        ).deleted_count
