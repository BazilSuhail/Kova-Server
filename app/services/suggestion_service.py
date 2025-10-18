"""Adaptive, habit-aware suggestions (feature 17).

Derived on read from tasks, mood logs, reflections, and reminders. Nothing is
learned/persisted yet — the rules are transparent and deterministic, which keeps
them safe to explain to the user and trivial to test.
"""
from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from ..repositories.mood_repository import MoodRepository
from ..repositories.reflection_repository import ReflectionRepository
from ..repositories.reminder_repository import ReminderRepository
from ..repositories.task_repository import TaskRepository


def _day(value: Any) -> str | None:
    return value[:10] if isinstance(value, str) and len(value) >= 10 else None


class SuggestionService:
    def __init__(
        self,
        tasks: TaskRepository,
        moods: MoodRepository,
        reflections: ReflectionRepository,
        reminders: ReminderRepository,
    ) -> None:
        self._tasks = tasks
        self._moods = moods
        self._reflections = reflections
        self._reminders = reminders

    def get(self, user_id: str) -> dict[str, Any]:
        now = datetime.now(UTC)
        today = now.date().isoformat()
        tasks = self._tasks.find_all(user_id)
        moods = self._moods.find_for_user(user_id, limit=7)
        reflections = self._reflections.find_for_user(user_id, limit=7)
        reminders = self._reminders.find_for_user(user_id, status="pending")

        pending = [t for t in tasks if not t.get("isCompleted")]
        suggestions: list[dict[str, Any]] = []

        overdue = [
            t for t in pending
            if (_day(t.get("dueDate")) or "9999") < today
        ]
        if overdue:
            suggestions.append(
                {
                    "id": "reschedule_overdue",
                    "type": "reschedule",
                    "priority": "high",
                    "title": "Reschedule what slipped",
                    "message": (
                        f"{len(overdue)} task(s) are past due — move them to a "
                        "realistic day so the list stays trustworthy."
                    ),
                }
            )

        if not any(_day(m.get("date") or m.get("loggedAt")) == today for m in moods):
            suggestions.append(
                {
                    "id": "log_mood",
                    "type": "wellbeing",
                    "priority": "low",
                    "title": "How are you feeling?",
                    "message": "Log your mood today to keep your trends meaningful.",
                }
            )

        recent_scores = [m.get("score", 3) for m in moods[:3]]
        if recent_scores and sum(recent_scores) / len(recent_scores) <= 2 and len(pending) > 5:
            suggestions.append(
                {
                    "id": "reduce_load",
                    "type": "load",
                    "priority": "medium",
                    "title": "Lighten today",
                    "message": (
                        "Your recent mood is low and the list is long — pick the "
                        "one task that matters most and defer the rest."
                    ),
                }
            )

        habit = self._busiest_weekday(tasks)
        if habit is not None:
            suggestions.append(
                {
                    "id": "habit_block",
                    "type": "habit",
                    "priority": "low",
                    "title": f"You usually plan on {habit}s",
                    "message": (
                        f"Most of your tasks are created on {habit} — block time "
                        "that day to plan the week."
                    ),
                }
            )

        due_today = [t for t in pending if _day(t.get("dueDate")) == today]
        if due_today and not reminders:
            suggestions.append(
                {
                    "id": "set_reminder",
                    "type": "reminder",
                    "priority": "medium",
                    "title": "Set a gentle nudge",
                    "message": (
                        f"{len(due_today)} task(s) are due today — add a reminder "
                        "so nothing slips through."
                    ),
                }
            )

        if tasks:
            ratio = len([t for t in tasks if t.get("isCompleted")]) / len(tasks)
            if ratio >= 0.7:
                suggestions.append(
                    {
                        "id": "momentum",
                        "type": "encouragement",
                        "priority": "low",
                        "title": "Momentum is real",
                        "message": (
                            f"You've completed {int(ratio * 100)}% of your tasks "
                            "— keep going."
                        ),
                    }
                )

        reflected_today = any(_day(r.get("date")) == today for r in reflections)
        did_work_today = any(_day(t.get("dueDate")) == today for t in tasks)
        if did_work_today and not reflected_today:
            suggestions.append(
                {
                    "id": "reflect_today",
                    "type": "reflection",
                    "priority": "low",
                    "title": "Close the loop",
                    "message": "Take a minute to write today's reflection.",
                }
            )

        return {"generatedAt": now.isoformat(), "suggestions": suggestions}

    @staticmethod
    def _busiest_weekday(tasks: list[dict[str, Any]]) -> str | None:
        counts: Counter[str] = Counter()
        for task in tasks:
            day = _day(task.get("createdAt"))
            if day is None:
                continue
            try:
                counts[datetime.fromisoformat(day).strftime("%A")] += 1
            except ValueError:
                continue
        if not counts:
            return None
        name, _ = counts.most_common(1)[0]
        return name
