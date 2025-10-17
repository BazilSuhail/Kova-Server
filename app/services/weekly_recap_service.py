"""Seven-day recap: per-day task splits and reflections for a rolling window.

Mirrors :class:`DailyRecapService` day-by-day (UTC), so the per-day entries keep
the exact shape the daily endpoint already returns.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ..core.exceptions import ValidationError
from ..repositories.planner_repository import PlannerRepository
from ..repositories.task_repository import TaskRepository

WEEK_DAYS = 7
_DATE_FORMAT = "%Y-%m-%d"


class WeeklyRecapService:
    def __init__(self, tasks: TaskRepository, planners: PlannerRepository) -> None:
        self._tasks = tasks
        self._planners = planners

    def get_recap(self, user_id: str, end: str | None = None) -> dict[str, Any]:
        """Aggregate the ``WEEK_DAYS`` days ending on ``end`` (default: today, UTC).

        ``end`` must be ``YYYY-MM-DD``; anything else is a client error (400).
        """
        end_date = self._parse_end(end).date()
        start_date = end_date - timedelta(days=WEEK_DAYS - 1)

        days: list[dict[str, Any]] = []
        completed_total = 0
        pending_total = 0
        offset = 0
        while offset < WEEK_DAYS:
            day = start_date + timedelta(days=offset)
            prefix = day.isoformat()
            tasks = self._tasks.find_due_on(user_id, prefix)
            completed = [t["title"] for t in tasks if t.get("isCompleted")]
            pending = [t["title"] for t in tasks if not t.get("isCompleted")]
            planner = self._planners.find_by_date(user_id, prefix)
            mood = "Not recorded"
            if planner is not None and planner.get("reflection"):
                mood = planner["reflection"]
            days.append(
                {
                    "date": prefix,
                    "completedTasks": completed,
                    "pendingTasks": pending,
                    "mood": mood,
                }
            )
            completed_total += len(completed)
            pending_total += len(pending)
            offset += 1

        return {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "days": days,
            "totals": {
                "completedTasks": completed_total,
                "pendingTasks": pending_total,
            },
        }

    @staticmethod
    def _parse_end(end: str | None) -> datetime:
        if end is None:
            return datetime.now(timezone.utc)
        try:
            return datetime.strptime(end, _DATE_FORMAT).replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValidationError("end must be a YYYY-MM-DD date") from exc
