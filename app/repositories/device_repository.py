"""Data access for the ``push_devices`` collection (feature 10 — delivery)."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class DeviceRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "push_devices")

    def find_by_token(self, expo_push_token: str) -> dict[str, Any] | None:
        """One row per physical device — the token is the unique key."""
        return self.find_one({"expoPushToken": expo_push_token})

    def find_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.find_many({"userId": user_id}, sort=("registeredAt", -1))

    def find_by_id_for_user(
        self, device_id: str, user_id: str
    ) -> dict[str, Any] | None:
        return self.find_one({"deviceId": device_id, "userId": user_id})

    def update_fields(self, device_id: str, fields: dict[str, Any]) -> int:
        return self.update({"deviceId": device_id}, fields).modified_count

    def delete_for_user(self, device_id: str, user_id: str) -> int:
        return self.delete_one(
            {"deviceId": device_id, "userId": user_id}
        ).deleted_count

    def delete_by_token(self, expo_push_token: str) -> int:
        """Drop a token Expo reported as unregistered (stale device cleanup)."""
        return self.delete_one({"expoPushToken": expo_push_token}).deleted_count
