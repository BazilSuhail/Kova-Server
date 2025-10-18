"""Offline sync: delta pull + last-write-wins push, with deletion tombstones.

Feature 14. Clients pull everything changed since their last cursor
(``updatedAt``) plus the ids deleted since then, so local edits and deletes
reconcile automatically on reconnect.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..repositories.mood_repository import MoodRepository
from ..repositories.notification_repository import NotificationRepository
from ..repositories.planner_repository import PlannerRepository
from ..repositories.reflection_repository import ReflectionRepository
from ..repositories.reminder_repository import ReminderRepository
from ..repositories.subtask_repository import SubtaskRepository
from ..repositories.summary_repository import SummaryRepository
from ..repositories.task_repository import TaskRepository
from ..repositories.tombstone_repository import TombstoneRepository

# collection name → (repository attribute, id field). Subtasks handled apart.
_SYNCED = (
    ("tasks", "tasks", "taskId"),
    ("planner", "planner", "plannerId"),
    ("summaries", "summaries", "summaryId"),
    ("notifications", "notifications", "notificationId"),
    ("mood", "moods", "moodId"),
    ("reflections", "reflections", "reflectionId"),
    ("reminders", "reminders", "reminderId"),
)


class SyncService:
    def __init__(
        self,
        tasks: TaskRepository,
        subtasks: SubtaskRepository,
        planner: PlannerRepository,
        summaries: SummaryRepository,
        notifications: NotificationRepository,
        moods: MoodRepository,
        reflections: ReflectionRepository,
        reminders: ReminderRepository,
        tombstones: TombstoneRepository,
    ) -> None:
        self._tasks = tasks
        self._subtasks = subtasks
        self._planner = planner
        self._summaries = summaries
        self._notifications = notifications
        self._moods = moods
        self._reflections = reflections
        self._reminders = reminders
        self._tombstones = tombstones
        self._repos = {
            "tasks": tasks,
            "planner": planner,
            "summaries": summaries,
            "notifications": notifications,
            "mood": moods,
            "reflections": reflections,
            "reminders": reminders,
        }

    # --- pull ---------------------------------------------------------------
    def pull(self, user_id: str, since: str | None = None) -> dict[str, Any]:
        task_ids = [task["taskId"] for task in self._tasks.find_all(user_id)]
        payload: dict[str, Any] = {
            "serverTime": datetime.now(UTC).isoformat(),
            "full": since is None,
            "since": since,
        }
        for name, _attr, _id in _SYNCED:
            payload[name] = self._repos[name].find_updated_since(user_id, since)
        payload["subtasks"] = (
            self._subtasks.find_since_by_tasks(task_ids, since) if task_ids else []
        )
        payload["deleted"] = self._tombstones.find_since(user_id, since)
        return payload

    # --- push ---------------------------------------------------------------
    def push(self, user_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        applied: dict[str, int] = {}
        skipped: list[dict[str, str]] = []

        for name, _attr, id_field in _SYNCED:
            repo = self._repos[name]
            count = 0
            for document in changes.get(name, []) or []:
                if self._upsert(repo, id_field, document, user_id):
                    count += 1
            applied[name] = count

        subtask_count = 0
        for document in changes.get("subtasks", []) or []:
            task_id = document.get("taskId", "")
            if self._tasks.find_for_user(task_id, user_id) is None:
                skipped.append({"collection": "subtasks", "reason": "unknown taskId"})
                continue
            if self._upsert(self._subtasks, "subtaskId", document, user_id):
                subtask_count += 1
        applied["subtasks"] = subtask_count

        deleted = 0
        for item in changes.get("deletions", []) or []:
            if self._apply_deletion(user_id, item):
                deleted += 1
        applied["deletions"] = deleted

        return {
            "applied": applied,
            "skipped": skipped,
            "serverTime": datetime.now(UTC).isoformat(),
        }

    def _upsert(
        self,
        repo: Any,
        id_field: str,
        document: dict[str, Any],
        user_id: str,
    ) -> bool:
        doc_id = document.get(id_field)
        if not doc_id:
            return False
        existing = repo.find_one({id_field: doc_id})
        fields = {k: v for k, v in document.items() if k != "_id"}
        if existing is not None:
            # Last-write-wins: a newer server copy beats a stale client edit.
            server_ts = existing.get("updatedAt")
            client_ts = document.get("updatedAt")
            if server_ts and client_ts and server_ts > client_ts:
                return False
            fields["userId"] = user_id
            repo.update({id_field: doc_id}, fields)
            return True
        fields["userId"] = user_id
        repo.insert(fields)
        return True

    def _apply_deletion(self, user_id: str, item: dict[str, Any]) -> bool:
        collection = item.get("collection", "")
        doc_id = item.get("id") or item.get("docId")
        if not collection or not doc_id:
            return False
        if collection == "subtasks":
            subtask = self._subtasks.find_by_subtask_id(doc_id)
            if subtask is None or self._tasks.find_for_user(
                subtask["taskId"], user_id
            ) is None:
                return False
            self._subtasks.delete_by_subtask_id(doc_id)
        else:
            entry = next((row for row in _SYNCED if row[0] == collection), None)
            if entry is None:
                return False
            id_field = entry[2]
            deleted = self._repos[collection].delete_one(
                {id_field: doc_id, "userId": user_id}
            ).deleted_count
            if not deleted:
                return False
        self._tombstones.record(
            user_id, collection, doc_id, datetime.now(UTC).isoformat()
        )
        return True
