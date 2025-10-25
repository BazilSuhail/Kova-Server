"""One-call home dashboard aggregation (feature 2).

The Expo client's home screen otherwise needs four round-trips (tasks, recap,
notifications, summaries); this bundles them without changing any existing
endpoint.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from ..core.timezone import local_now
from ..repositories.mood_repository import MoodRepository
from ..repositories.notification_repository import NotificationRepository
from ..repositories.reminder_repository import ReminderRepository
from ..repositories.summary_repository import SummaryRepository
from ..repositories.task_repository import TaskRepository
from .mood_service import MoodService
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
        mood_service: MoodService,
    ) -> None:
        self._tasks = tasks
        self._notifications = notifications
        self._reminders = reminders
        self._moods = moods
        self._summaries = summaries
        self._progress = progress
        self._suggestions = suggestions
        self._mood_service = mood_service

    def get(self, user_id: str) -> dict[str, Any]:
        now = local_now()
        today = now.date().isoformat()

        tasks = self._tasks.find_all(user_id)
        completed = [t for t in tasks if t.get("isCompleted")]
        pending = [t for t in tasks if not t.get("isCompleted")]
        today_tasks = [
            t for t in tasks if isinstance(t.get("dueDate"), str) and t["dueDate"].startswith(today)
        ]

        today_completed = sum(1 for t in today_tasks if t.get("isCompleted"))
        week = [(now.date() - timedelta(days=offset)).isoformat() for offset in range(6, -1, -1)]
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
            "nextReminders": self._reminders.find_upcoming(
                user_id, datetime.now(UTC).isoformat()
            )[:5],
            "latestMood": latest_mood[0] if latest_mood else None,
            "latestSummary": summaries[0] if summaries else None,
            "streak": self._progress.get_summary(user_id)["streak"]["current"],
            "suggestions": self._suggestions.get(user_id)["suggestions"],
            # Additive home-screen fields (keep the keys above stable).
            "todayProgress": {
                "total": len(today_tasks),
                "completed": today_completed,
                "pending": len(today_tasks) - today_completed,
            },
            # Bucketed by dueDate (tasks carry no completion timestamp), oldest first.
            "weeklyCompletion": [
                {
                    "date": day,
                    "completed": sum(
                        1 for t in tasks if _due_day(t) == day and t.get("isCompleted")
                    ),
                    "total": sum(1 for t in tasks if _due_day(t) == day),
                }
                for day in week
            ],
            "moodTrend": self._mood_service.trends(user_id, days=7)["series"],
            "recentSummaries": summaries[:3],
        }


def _due_day(task: dict[str, Any]) -> str | None:
    due = task.get("dueDate")
    return due[:10] if isinstance(due, str) and len(due) >= 10 else None
