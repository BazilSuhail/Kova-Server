"""One-call home dashboard aggregation (feature 2).

The Expo client's home screen otherwise needs four round-trips (tasks, recap,
notifications, summaries); this bundles them without changing any existing
endpoint.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..repositories.mood_repository import MoodRepository
from ..repositories.notification_repository import NotificationRepository
from ..repositories.reminder_repository import ReminderRepository
from ..repositories.summary_repository import SummaryRepository
from ..repositories.task_repository import TaskRepository
from .progress_service import ProgressService
from .suggestion_service import SuggestionService


class DashboardService:
    def __init__(
        self,
        tasks: TaskRepository,
        notifications: NotificationRepository,
        reminders: ReminderRepository,
        moods: MoodRepository,
        summaries: SummaryRepository,
        progress: ProgressService,
        suggestions: SuggestionService,
    ) -> None:
        self._tasks = tasks
        self._notifications = notifications
        self._reminders = reminders
        self._moods = moods
        self._summaries = summaries
        self._progress = progress
        self._suggestions = suggestions

    def get(self, user_id: str) -> dict[str, Any]:
        now = datetime.now(UTC)
        today = now.date().isoformat()

        tasks = self._tasks.find_all(user_id)
        completed = [t for t in tasks if t.get("isCompleted")]
        pending = [t for t in tasks if not t.get("isCompleted")]
        today_tasks = [
            t for t in tasks if isinstance(t.get("dueDate"), str) and t["dueDate"].startswith(today)
        ]

        latest_mood = self._moods.find_for_user(user_id, limit=1)
        summaries = self._summaries.find_for_user(user_id)

        return {
            "date": now.isoformat(),
            "tasks": {
                "total": len(tasks),
                "completed": len(completed),
                "pending": len(pending),
                "dueToday": len(today_tasks),
            },
            "todayTasks": today_tasks,
            "unreadNotifications": self._notifications.count_for_user(
                user_id, {"read": False}
            ),
            "nextReminders": self._reminders.find_upcoming(user_id, now.isoformat())[:5],
            "latestMood": latest_mood[0] if latest_mood else None,
            "latestSummary": summaries[0] if summaries else None,
            "streak": self._progress.get_summary(user_id)["streak"]["current"],
            "suggestions": self._suggestions.get(user_id)["suggestions"],
        }
