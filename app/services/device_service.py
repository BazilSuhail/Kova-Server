"""Push-device registration for reminder delivery (feature 10)."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from ..core.exceptions import ValidationError
from ..repositories.device_repository import DeviceRepository


class DeviceService:
    def __init__(self, devices: DeviceRepository) -> None:
        self._devices = devices

    def register(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Register or move an Expo push token to the caller.

        One physical device = one row: a token that already exists is re-owned
        (e.g. a user logged in on a shared phone) rather than duplicated.
        """
        token = str(data["expoPushToken"]).strip()
        platform = str(data.get("platform", "")).strip().lower()
        if platform and platform not in ("ios", "android", "web"):
            raise ValidationError("platform must be one of: ios, android, web")

        existing = self._devices.find_by_token(token)
        if existing is not None:
            self._devices.update_fields(
                existing["deviceId"],
                {
                    "userId": user_id,
                    "platform": platform or existing.get("platform", ""),
                    "enabled": True,
                },
            )
            return self._devices.find_by_id_for_user(existing["deviceId"], user_id) or {
                **existing,
                "userId": user_id,
            }

        document = {
            "deviceId": str(ObjectId()),
            "userId": user_id,
            "expoPushToken": token,
            "platform": platform,
            "enabled": True,
            "registeredAt": datetime.now(UTC).isoformat(),
        }
        return self._devices.insert(document)

    def list(self, user_id: str) -> list[dict[str, Any]]:
        return self._devices.find_for_user(user_id)

    def delete(self, user_id: str, device_id: str) -> bool:
        return self._devices.delete_for_user(device_id, user_id) > 0
