"""In-app notifications (reminders, task events) for the current user."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from ..core.query import PageParams, page_payload
from ..repositories.notification_repository import NotificationRepository

# Whitelist for partial updates — read state plus human-editable text.
_UPDATABLE_FIELDS = ("read", "title", "message", "triggerTime")


class NotificationService:
    def __init__(
        self, notifications: NotificationRepository, tombstones: object | None = None
    ) -> None:
        self._notifications = notifications
        self._tombstones = tombstones

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create an unread notification (route validated title/message)."""
        document = {
            "notificationId": str(ObjectId()),
            "userId": user_id,
            "title": data["title"],
            "message": data["message"],
            "type": data.get("type", ""),
            "relatedId": data.get("relatedId", ""),
            "createdAt": datetime.now(UTC).isoformat(),
            "read": False,
            "triggerTime": data.get("triggerTime"),
        }
        return self._notifications.insert(document)

    def list(
        self,
        user_id: str,
        *,
        unread: bool | None = None,
        page: PageParams | None = None,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Feed listing; ``unread=true`` filters, ``page`` switches to the envelope."""
        extra: dict[str, Any] | None = (
            None if unread is None else {"read": not unread}
        )
        if page is None:
            return self._notifications.find_for_user(user_id, extra)
        total = self._notifications.count_for_user(user_id, extra)
        items = self._notifications.find_page_for_user(
            user_id, extra, skip=page.skip, limit=page.limit
        )
        return page_payload(items, total, page)

    def get(self, notification_id: str, user_id: str) -> dict[str, Any] | None:
        return self._notifications.find_by_id_for_user(notification_id, user_id)

    def delete(self, notification_id: str, user_id: str) -> bool:
        deleted = self._notifications.delete_for_user(notification_id, user_id) > 0
        if deleted and self._tombstones is not None:
            self._tombstones.record(  # type: ignore[attr-defined]
                user_id, "notifications", notification_id, datetime.now(UTC).isoformat()
            )
        return deleted

    def update(self, notification_id: str, user_id: str, data: dict[str, Any]) -> bool:
        """Partial update; False covers both "missing" and "no change made"."""
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        return self._notifications.update_fields(notification_id, user_id, fields) > 0
