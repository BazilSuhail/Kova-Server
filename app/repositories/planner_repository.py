"""Data access for the ``planner`` collection (one document per day per user)."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class PlannerRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "planner")

    def find_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.find_many({"userId": user_id})

    def find_by_id_for_user(
        self, planner_id: str, user_id: str
    ) -> dict[str, Any] | None:
        """Ownership-checked lookup used before full updates."""
        return self.find_one({"plannerId": planner_id, "userId": user_id})

    def find_by_date(self, user_id: str, date_prefix: str) -> dict[str, Any] | None:
        """Locate a day's planner; ``date`` may be ``YYYY-MM-DD`` or full ISO."""
        return self.find_one(
            {"userId": user_id, "date": {"$regex": f"^{date_prefix}"}}
        )

    def update_fields(self, planner_id: str, user_id: str, fields: dict[str, Any]) -> int:
        return self.update(
            {"plannerId": planner_id, "userId": user_id}, fields
        ).modified_count

    def delete(self, planner_id: str, user_id: str) -> int:
        return self.delete_one({"plannerId": planner_id, "userId": user_id}).deleted_count
