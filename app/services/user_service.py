"""User profile reads/updates/deletes — the account **and everything it owns**."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..core.exceptions import NotFoundError, ValidationError
from ..repositories.user_repository import UserRepository
from ..utils.avatars import resolve_avatar_id

if TYPE_CHECKING:
    from ..repositories.device_repository import DeviceRepository
    from ..repositories.mood_repository import MoodRepository
    from ..repositories.notification_repository import NotificationRepository
    from ..repositories.planner_repository import PlannerRepository
    from ..repositories.reflection_repository import ReflectionRepository
    from ..repositories.reminder_repository import ReminderRepository
    from ..repositories.subtask_repository import SubtaskRepository
    from ..repositories.summary_repository import SummaryRepository
    from ..repositories.task_repository import TaskRepository
    from ..repositories.token_blocklist_repository import TokenBlocklistRepository
    from ..repositories.tombstone_repository import TombstoneRepository

# Fields a client may change directly — anything else is dropped.
_UPDATABLE_FIELDS = ("name", "email", "profilePicture", "preferences")

# Customisation keys accepted by the dedicated settings endpoint (feature 15).
_SETTING_FIELDS = (
    "theme",
    "fontSize",
    "layout",
    "notificationStyle",
    "notificationsEnabled",
    "language",
)


class UserService:
    def __init__(
        self,
        users: UserRepository,
        tasks: TaskRepository | None = None,
        subtasks: SubtaskRepository | None = None,
        planners: PlannerRepository | None = None,
        summaries: SummaryRepository | None = None,
        notifications: NotificationRepository | None = None,
        moods: MoodRepository | None = None,
        reflections: ReflectionRepository | None = None,
        devices: DeviceRepository | None = None,
        reminders: ReminderRepository | None = None,
        tombstones: TombstoneRepository | None = None,
        blocklist: TokenBlocklistRepository | None = None,
    ) -> None:
        self._users = users
        self._tasks = tasks
        self._subtasks = subtasks
        self._planners = planners
        self._summaries = summaries
        self._notifications = notifications
        self._moods = moods
        self._reflections = reflections
        self._devices = devices
        self._reminders = reminders
        self._tombstones = tombstones
        self._blocklist = blocklist

    def get_profile(self, user_id: str) -> dict[str, Any]:
        user = self._users.find_by_user_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def update_profile(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Apply whitelisted changes and return the refreshed profile.

        An ``avatarId`` (a server-hosted avatar from the catalogue) is resolved
        to its URL and stored in ``profilePicture``; an unknown id is rejected.
        ``modified_count == 0`` covers both "no such user" and "nothing
        actually changed" — the legacy service merged both into one 400 and
        that ambiguity is preserved deliberately.
        """
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        if "avatarId" in data:
            avatar_url = resolve_avatar_id(str(data["avatarId"]))
            if avatar_url is None:
                raise ValidationError("Unknown avatar")
            fields["profilePicture"] = avatar_url
        if "email" in fields and self._users.email_used_by_other_user(
            fields["email"], user_id
        ):
            raise ValidationError("Email already in use")
        if self._users.update_fields(user_id, fields) == 0:
            raise ValidationError("User not found or no changes made")
        return self.get_profile(user_id)

    def delete_profile(self, user_id: str) -> dict[str, int]:
        """Delete the account **and cascade-delete all owned content**.

        Returns the per-collection deleted counts. Related rows used to be
        orphaned; a mobile client that deletes its account expects the data to
        actually be gone, so the cascade is now part of the contract.
        """
        if self._users.find_by_user_id(user_id) is None:
            raise NotFoundError("User not found")

        deleted: dict[str, int] = {}

        # Subtasks are owner-less, so resolve them through the user's task ids.
        task_ids = (
            [t["taskId"] for t in self._tasks.find_all(user_id) if t.get("taskId")]
            if self._tasks is not None
            else []
        )
        if self._subtasks is not None and task_ids:
            deleted["subtasks"] = self._subtasks.delete_many(
                {"taskId": {"$in": task_ids}}
            ).deleted_count

        owned: tuple[tuple[str, Any], ...] = (
            ("tasks", self._tasks),
            ("planner", self._planners),
            ("summaries", self._summaries),
            ("notifications", self._notifications),
            ("mood", self._moods),
            ("reflections", self._reflections),
            ("devices", self._devices),
            ("reminders", self._reminders),
            ("tombstones", self._tombstones),
            ("blocklist", self._blocklist),
        )
        for name, repository in owned:
            if repository is not None:
                deleted[name] = repository.delete_many({"userId": user_id}).deleted_count

        self._users.delete_by_user_id(user_id)
        return deleted

    def get_settings(self, user_id: str) -> dict[str, Any]:
        """Return the customisation block (feature 15)."""
        profile = self.get_profile(user_id)
        return dict(profile.get("preferences") or {})

    def update_settings(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Merge whitelisted settings into ``preferences`` and return the result."""
        profile = self.get_profile(user_id)
        preferences = dict(profile.get("preferences") or {})
        for key, value in data.items():
            if key in _SETTING_FIELDS:
                preferences[key] = value
        self._users.update_fields(user_id, {"preferences": preferences})
        return preferences
