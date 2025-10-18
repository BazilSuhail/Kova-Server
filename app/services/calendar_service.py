"""Calendar views (day/week/month) over tasks + planner (feature 5).

Read-only aggregation: no new storage. Returns each day in the window with its
tasks and planner document so the client can render any view without extra
round-trips.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from ..core.exceptions import ValidationError
from ..repositories.planner_repository import PlannerRepository
from ..repositories.task_repository import TaskRepository

_VIEWS = ("day", "week", "month")


def _parse_date(raw: str | None) -> date:
    if raw is None:
        return datetime.now(UTC).date()
    try:
        return datetime.fromisoformat(raw[:10]).date()
    except ValueError as exc:
        raise ValidationError("date must be a YYYY-MM-DD date") from exc


class CalendarService:
    def __init__(self, tasks: TaskRepository, planners: PlannerRepository) -> None:
        self._tasks = tasks
        self._planners = planners

    def get(
        self, user_id: str, *, view: str = "week", day: str | None = None
    ) -> dict[str, Any]:
        view = view.lower()
        if view not in _VIEWS:
            raise ValidationError("view must be one of: day, week, month")

        anchor = _parse_date(day)
        start, end = self._window(view, anchor)
        after_end = (end + timedelta(days=1)).isoformat()

        tasks = self._tasks.find_many(
            {
                "userId": user_id,
                "dueDate": {"$gte": start.isoformat(), "$lt": after_end},
            }
        )
        planner_by_day: dict[str, dict[str, Any]] = {}
        for entry in self._planners.find_many(
            {
                "userId": user_id,
                "date": {"$gte": start.isoformat(), "$lt": after_end},
            }
        ):
            planner_by_day.setdefault((entry.get("date") or "")[:10], entry)

        days: list[dict[str, Any]] = []
        cursor = start
        while cursor <= end:
            prefix = cursor.isoformat()
            days.append(
                {
                    "date": prefix,
                    "tasks": [
                        task
                        for task in tasks
                        if isinstance(task.get("dueDate"), str)
                        and task["dueDate"].startswith(prefix)
                    ],
                    "planner": planner_by_day.get(prefix),
                }
            )
            cursor += timedelta(days=1)

        return {
            "view": view,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": days,
        }

    @staticmethod
    def _window(view: str, anchor: date) -> tuple[date, date]:
        if view == "day":
            return anchor, anchor
        if view == "month":
            start = anchor.replace(day=1)
            next_month = (start + timedelta(days=31)).replace(day=1)
            return start, next_month - timedelta(days=1)
        # week: ISO week starting Monday
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=6)
