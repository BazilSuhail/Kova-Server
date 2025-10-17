"""Data access for the ``summaries`` collection (PDF-derived bullet summaries)."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class SummaryRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "summaries")

    def find_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.find_many({"userId": user_id})

    def update_fields(self, summary_id: str, user_id: str, fields: dict[str, Any]) -> int:
        return self.update(
            {"summaryId": summary_id, "userId": user_id}, fields
        ).modified_count

    def delete(self, summary_id: str, user_id: str) -> int:
        return self.delete_one({"summaryId": summary_id, "userId": user_id}).deleted_count
