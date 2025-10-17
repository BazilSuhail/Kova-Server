"""Data access for the ``notifications`` collection."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "notifications")

    def find_for_user(self, user_id: str) -> list[dict[str, Any]]:
        """Newest first — the feed order the client renders."""
        return self.find_many({"userId": user_id}, sort=("createdAt", -1))

    def update_fields(
        self, notification_id: str, user_id: str, fields: dict[str, Any]
    ) -> int:
        return self.update(
            {"notificationId": notification_id, "userId": user_id}, fields
        ).modified_count
