"""Personal progress: completion stats, streaks, load balance, achievements.

Feature 13. Everything is derived on read from existing collections — no extra
writes, so it can never drift from the task/mood/journal data.
"""
from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from ..repositories.mood_repository import MoodRepository
from ..repositories.reflection_repository import ReflectionRepository
from ..repositories.task_repository import TaskRepository

_WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _day_of(*candidates: Any) -> str | None:
    for value in candidates:
        if isinstance(value, str) and len(value) >= 10:
            return value[:10]
    return None


class ProgressService:
    def __init__(
        self,
        tasks: TaskRepository,
        moods: MoodRepository,
        reflections: ReflectionRepository,
    ) -> None:
        self._tasks = tasks
        self._moods = moods
        self._reflections = reflections

    def get_summary(self, user_id: str) -> dict[str, Any]:
        tasks = self._tasks.find_all(user_id)
        moods = self._moods.find_for_user(user_id)
        reflections = self._reflections.find_for_user(user_id)

        completed = [task for task in tasks if task.get("isCompleted")]
        total = len(tasks)
        completion_rate = round(len(completed) / total, 2) if total else 0.0

        active_days = self._active_days(completed, moods, reflections)
        streak = self._streak(active_days)

        return {
            "totals": {
                "tasks": total,
                "completedTasks": len(completed),
                "pendingTasks": total - len(completed),
                "completionRate": completion_rate,
                "moodEntries": len(moods),
                "reflections": len(reflections),
            },
            "streak": {"current": streak, "longest": self._longest_run(active_days)},
            "loadBalance": self._load_balance(tasks),
            "achievements": self._achievements(
                total, completed, streak, len(moods), len(reflections)
            ),
            "activeDays": len(active_days),
        }

    @staticmethod
    def _active_days(
        completed: list[dict[str, Any]],
        moods: list[dict[str, Any]],
        reflections: list[dict[str, Any]],
    ) -> set[str]:
        days: set[str] = set()
        for task in completed:
            day = _day_of(task.get("dueDate"), task.get("createdAt"))
            if day:
                days.add(day)
        for entry in moods:
            day = _day_of(entry.get("date"), entry.get("loggedAt"))
            if day:
                days.add(day)
        for reflection in reflections:
            day = _day_of(reflection.get("date"))
            if day:
                days.add(day)
        return days

    @staticmethod
    def _streak(active_days: set[str]) -> int:
        streak = 0
        cursor = datetime.now(UTC).date()
        while cursor.isoformat() in active_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    @staticmethod
    def _longest_run(active_days: set[str]) -> int:
        longest = 0
        for day in active_days:
            try:
                start = datetime.fromisoformat(day).date()
            except ValueError:
                continue
            # Only count a run from its first day (previous day inactive).
            if (start - timedelta(days=1)).isoformat() in active_days:
                continue
            run = 0
            cursor = start
            while cursor.isoformat() in active_days:
                run += 1
                cursor += timedelta(days=1)
            longest = max(longest, run)
        return longest

    @staticmethod
    def _load_balance(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Completed vs pending per weekday, based on ``dueDate`` (last 7 days)."""
        end = datetime.now(UTC).date()
        start = end - timedelta(days=6)
        completed: Counter[str] = Counter()
        pending: Counter[str] = Counter()
        for task in tasks:
            day = _day_of(task.get("dueDate"))
            if day is None or day < start.isoformat() or day > end.isoformat():
                continue
            try:
                weekday = datetime.fromisoformat(day).strftime("%a")
            except ValueError:
                continue
            (completed if task.get("isCompleted") else pending)[weekday] += 1
        return [
            {
                "day": _WEEKDAY_NAMES[offset],
                "completed": completed[_WEEKDAY_NAMES[offset]],
                "pending": pending[_WEEKDAY_NAMES[offset]],
            }
            for offset in range(7)
        ]

    @staticmethod
    def _achievements(
        total: int,
        completed: list[dict[str, Any]],
        streak: int,
        mood_entries: int,
        reflections: int,
    ) -> list[dict[str, Any]]:
        def item(key: str, label: str, value: int, target: int) -> dict[str, Any]:
            return {
                "id": key,
                "label": label,
                "earned": value >= target,
                "progress": min(value, target),
                "target": target,
            }

        return [
            item("first_task", "Created your first task", total, 1),
            item("ten_tasks", "Created 10 tasks", total, 10),
            item("fifty_tasks", "Created 50 tasks", total, 50),
            item("ten_done", "Completed 10 tasks", len(completed), 10),
            item("streak_3", "3-day streak", streak, 3),
            item("streak_7", "7-day streak", streak, 7),
            item("mood_7", "Logged mood 7 times", mood_entries, 7),
            item("reflections_5", "Wrote 5 reflections", reflections, 5),
        ]
