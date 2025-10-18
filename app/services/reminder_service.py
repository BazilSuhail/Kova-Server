"""Scheduled, gentle reminders delivered as notifications + push (feature 10)."""
from __future__ import annotations

import builtins
from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId

from ..core.exceptions import NotFoundError, ValidationError
from ..repositories.device_repository import DeviceRepository
from ..repositories.reminder_repository import ReminderRepository
from ..utils.push_client import send_push
from .notification_service import NotificationService


def _normalize_fire_at(raw: Any) -> str:
    """Accept ``YYYY-MM-DD`` or an ISO datetime; return a UTC ISO timestamp."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValidationError("fireAt must be an ISO date or datetime")
    text = raw.strip()
    if len(text) == 10:
        text = f"{text}T09:00:00+00:00"  # date-only → 9am UTC default
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError("fireAt must be an ISO date or datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat()


class ReminderService:
    def __init__(
        self,
        reminders: ReminderRepository,
        devices: DeviceRepository,
        notifications: NotificationService,
        tombstones: Any = None,
    ) -> None:
        self._reminders = reminders
        self._devices = devices
        self._notifications = notifications
        self._tombstones = tombstones

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Schedule a reminder for the caller."""
        now = datetime.now(UTC).isoformat()
        document = {
            "reminderId": str(ObjectId()),
            "userId": user_id,
            "title": data["title"],
            "message": data.get("message", ""),
            "fireAt": _normalize_fire_at(data.get("fireAt")),
            "relatedType": data.get("relatedType", ""),
            "relatedId": data.get("relatedId", ""),
            "status": "pending",
            "createdAt": now,
        }
        return self._reminders.insert(document)

    def list(
        self, user_id: str, *, status: str | None = None
    ) -> list[dict[str, Any]]:
        return self._reminders.find_for_user(user_id, status=status)

    def upcoming(self, user_id: str, *, hours: int = 48) -> builtins.list[dict[str, Any]]:
        horizon = (datetime.now(UTC) + timedelta(hours=hours)).isoformat()
        return [
            reminder
            for reminder in self._reminders.find_upcoming(
                user_id, datetime.now(UTC).isoformat()
            )
            if reminder.get("fireAt", "") <= horizon
        ]

    def get(self, user_id: str, reminder_id: str) -> dict[str, Any]:
        reminder = self._reminders.find_by_id_for_user(reminder_id, user_id)
        if reminder is None:
            raise NotFoundError("Reminder not found")
        return reminder

    def delete(self, user_id: str, reminder_id: str) -> bool:
        deleted = self._reminders.delete_for_user(reminder_id, user_id) > 0
        if deleted and self._tombstones is not None:
            self._tombstones.record(
                user_id, "reminders", reminder_id, datetime.now(UTC).isoformat()
            )
        return deleted

    def deliver_due(self) -> int:
        """Fire every pending reminder whose time has come.

        For each due reminder: create an in-app notification, push to every
        registered device, prune tokens Expo reports as unregistered, then mark
        the reminder ``sent``. Returns how many fired.
        """
        due = self._reminders.find_due(datetime.now(UTC).isoformat())
        for reminder in due:
            user_id = reminder["userId"]
            self._notifications.create(
                user_id,
                {
                    "title": reminder["title"],
                    "message": reminder.get("message", ""),
                    "type": "reminder",
                    "relatedId": reminder.get("relatedId", ""),
                },
            )
            devices = self._devices.find_for_user(user_id)
            messages = [
                {
                    "to": device["expoPushToken"],
                    "title": reminder["title"],
                    "body": reminder.get("message", ""),
                    "data": {"reminderId": reminder["reminderId"]},
                }
                for device in devices
                if device.get("expoPushToken")
            ]
            for token in send_push(messages):
                self._devices.delete_by_token(token)
            self._reminders.update_fields(
                reminder["reminderId"],
                {"status": "sent", "sentAt": datetime.now(UTC).isoformat()},
            )
        return len(due)
