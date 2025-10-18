"""Mood journal, trends, and mood-based load suggestions (features 6 & 12)."""
from __future__ import annotations

import builtins
from datetime import UTC, date, datetime, timedelta
from statistics import mean
from typing import Any

from bson import ObjectId

from ..core.exceptions import NotFoundError
from ..core.query import PageParams, page_payload
from ..repositories.mood_repository import MoodRepository

# Label → 1..5 score, used when the client does not send an explicit score.
MOOD_SCORES: dict[str, int] = {
    "awful": 1,
    "bad": 2,
    "low": 2,
    "okay": 3,
    "ok": 3,
    "neutral": 3,
    "good": 4,
    "great": 5,
    "amazing": 5,
}
DEFAULT_SCORE = 3

# Load guidance per score band (feature 6 — mood-based suggestion).
_LOAD_GUIDANCE = {
    1: ("light", "Protect your energy today: pick one essential task and let the rest wait."),
    2: ("light", "Keep today gentle — two or three small tasks, with breaks."),
    3: ("balanced", "A normal day: mix a few task types and keep the list realistic."),
    4: ("stretch", "Good energy — a great day to tackle that one task you keep postponing."),
    5: ("stretch", "High energy: take on the hardest task first while focus is peak."),
}


class MoodService:
    def __init__(self, moods: MoodRepository, tombstones: Any = None) -> None:
        self._moods = moods
        self._tombstones = tombstones

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Log a mood entry (route validated ``mood`` presence)."""
        logged_at = datetime.now(UTC)
        mood = str(data["mood"]).strip()
        score = data.get("score")
        if not isinstance(score, int) or not 1 <= score <= 5:
            score = MOOD_SCORES.get(mood.lower(), DEFAULT_SCORE)
        energy = data.get("energy")
        if not isinstance(energy, int) or not 1 <= energy <= 5:
            energy = None
        tags = data.get("tags")
        document = {
            "moodId": str(ObjectId()),
            "userId": user_id,
            "mood": mood,
            "score": score,
            "energy": energy,
            "note": data.get("note", ""),
            "tags": tags if isinstance(tags, list) else [],
            "loggedAt": logged_at.isoformat(),
            "date": logged_at.date().isoformat(),
            "createdAt": logged_at.isoformat(),
        }
        return self._moods.insert(document)

    def list(
        self, user_id: str, *, page: PageParams | None = None
    ) -> list[dict[str, Any]] | dict[str, Any]:
        if page is None:
            return self._moods.find_for_user(user_id)
        rows = self._moods.find_for_user(user_id)
        total = len(rows)
        return page_payload(rows[page.skip : page.skip + page.limit], total, page)

    def latest(self, user_id: str) -> dict[str, Any] | None:
        rows = self._moods.find_for_user(user_id, limit=1)
        return rows[0] if rows else None

    def trends(self, user_id: str, *, days: int = 30) -> dict[str, Any]:
        """Aggregate the last ``days`` of mood logs into a trend payload."""
        end = datetime.now(UTC).date()
        start = end - timedelta(days=days - 1)
        start_prefix = f"{start.isoformat()}T00:00:00"
        end_prefix = f"{(end + timedelta(days=1)).isoformat()}T00:00:00"
        entries = self._moods.find_in_window(user_id, start_prefix, end_prefix)

        by_day: dict[str, list[int]] = {}
        distribution: dict[str, int] = {}
        for entry in entries:
            by_day.setdefault(entry.get("date", ""), []).append(entry.get("score", DEFAULT_SCORE))
            label = entry.get("mood", "unknown")
            distribution[label] = distribution.get(label, 0) + 1

        series: list[dict[str, Any]] = []
        for offset in range(days):
            day = (start + timedelta(days=offset)).isoformat()
            day_scores = by_day.get(day, [])
            series.append(
                {
                    "date": day,
                    "score": round(mean(day_scores), 2) if day_scores else None,
                    "entries": len(day_scores),
                }
            )

        scores = [entry.get("score", DEFAULT_SCORE) for entry in entries]
        return {
            "range": {"start": start.isoformat(), "end": end.isoformat(), "days": days},
            "entries": len(entries),
            "averageScore": round(mean(scores), 2) if scores else None,
            "distribution": distribution,
            "series": series,
            "streak": self._logging_streak(by_day, end),
        }

    def load_suggestion(
        self,
        user_id: str,
        *,
        mood: str | None = None,
        energy: int | None = None,
    ) -> dict[str, Any]:
        """Recommend a task load from the latest (or supplied) mood (feature 6)."""
        score = MOOD_SCORES.get(mood.lower(), DEFAULT_SCORE) if mood else None
        if score is None:
            latest = self.latest(user_id)
            score = latest.get("score", DEFAULT_SCORE) if latest else DEFAULT_SCORE
            if energy is None and latest:
                energy = latest.get("energy")
        load, message = _LOAD_GUIDANCE[score]
        return {
            "score": score,
            "energy": energy,
            "suggestedLoad": load,
            "message": message,
        }

    def delete(self, user_id: str, mood_id: str) -> bool:
        deleted = self._moods.delete_for_user(mood_id, user_id) > 0
        if deleted and self._tombstones is not None:
            self._tombstones.record(user_id, "mood", mood_id, datetime.now(UTC).isoformat())
        return deleted

    @staticmethod
    def _logging_streak(by_day: dict[str, builtins.list[int]], end: date) -> int:
        """Consecutive days (ending today) that have at least one logged mood."""
        streak = 0
        cursor = end
        while by_day.get(cursor.isoformat()):
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def get(self, user_id: str, mood_id: str) -> dict[str, Any]:
        entry = self._moods.find_by_id_for_user(mood_id, user_id)
        if entry is None:
            raise NotFoundError("Mood entry not found")
        return entry
