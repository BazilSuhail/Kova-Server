"""Data access for the ``notifications`` collection."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "notifications")

    def find_for_user(
        self, user_id: str, extra: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Newest first — the feed order the client renders."""
        query = {"userId": user_id}
        if extra:
            query.update(extra)
        return self.find_many(query, sort=("createdAt", -1))

    def find_page_for_user(
        self,
        user_id: str,
        extra: dict[str, Any] | None,
        *,
        skip: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        query = {"userId": user_id}
        if extra:
            query.update(extra)
        return self.find_page(query, sort=("createdAt", -1), skip=skip, limit=limit)

    def count_for_user(self, user_id: str, extra: dict[str, Any] | None = None) -> int:
        query = {"userId": user_id}
        if extra:
            query.update(extra)
        return self.count(query)

    def find_by_id_for_user(
        self, notification_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return self.find_one(
            {"notificationId": notification_id, "userId": user_id}
        )

    def delete_for_user(self, notification_id: str, user_id: str) -> int:
        return self.delete_one(
            {"notificationId": notification_id, "userId": user_id}
        ).deleted_count

    def update_fields(
        self, notification_id: str, user_id: str, fields: dict[str, Any]
    ) -> int:
        return self.update(
            {"notificationId": notification_id, "userId": user_id}, fields
        ).modified_count
