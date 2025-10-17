"""In-app notifications (reminders, task events) for the current user."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from ..repositories.notification_repository import NotificationRepository

# Whitelist for partial updates — read state plus human-editable text.
_UPDATABLE_FIELDS = ("read", "title", "message", "triggerTime")


class NotificationService:
    def __init__(self, notifications: NotificationRepository) -> None:
        self._notifications = notifications

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create an unread notification (route validated title/message)."""
        document = {
            "notificationId": str(ObjectId()),
            "userId": user_id,
            "title": data["title"],
            "message": data["message"],
            "type": data.get("type", ""),
            "relatedId": data.get("relatedId", ""),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "triggerTime": data.get("triggerTime"),
        }
        return self._notifications.insert(document)

    def list(self, user_id: str) -> list[dict[str, Any]]:
        return self._notifications.find_for_user(user_id)

    def update(self, notification_id: str, user_id: str, data: dict[str, Any]) -> bool:
        """Partial update; False covers both "missing" and "no change made"."""
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        return self._notifications.update_fields(notification_id, user_id, fields) > 0
