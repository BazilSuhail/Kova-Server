"""Daily reflection prompts, journaling, and affirmations (feature 18)."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from ..core.exceptions import NotFoundError
from ..repositories.reflection_repository import ReflectionRepository
from ..utils.affirmations import affirmation_for, prompt_for


class ReflectionService:
    def __init__(self, reflections: ReflectionRepository, tombstones: Any = None) -> None:
        self._reflections = reflections
        self._tombstones = tombstones

    def today(self, user_id: str, day: str | None = None) -> dict[str, Any]:
        """Today's prompt + affirmation, plus the entry if already written."""
        target = day or datetime.now(UTC).date().isoformat()
        return {
            "date": target,
            "prompt": prompt_for(target),
            "affirmation": affirmation_for(target),
            "reflection": self._reflections.find_by_date(user_id, target),
        }

    def log(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create or replace today's (or ``data['date']``'s) reflection entry."""
        now = datetime.now(UTC)
        target = data.get("date") or now.date().isoformat()
        existing = self._reflections.find_by_date(user_id, target)
        fields = {
            "text": data["text"],
            "mood": data.get("mood", ""),
            "prompt": data.get("prompt", prompt_for(target)),
            "date": target,
        }
        if existing is not None:
            self._reflections.update_fields(existing["reflectionId"], user_id, fields)
            updated = self._reflections.find_by_id_for_user(existing["reflectionId"], user_id)
            return updated or {**existing, **fields}
        document = {
            "reflectionId": str(ObjectId()),
            "userId": user_id,
            **fields,
            "affirmation": affirmation_for(target),
            "createdAt": now.isoformat(),
        }
        return self._reflections.insert(document)

    def list(self, user_id: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        return self._reflections.find_for_user(user_id, limit=limit)

    def delete(self, user_id: str, reflection_id: str) -> bool:
        deleted = self._reflections.delete_for_user(reflection_id, user_id) > 0
        if deleted and self._tombstones is not None:
            self._tombstones.record(
                user_id, "reflections", reflection_id, datetime.now(UTC).isoformat()
            )
        return deleted

    def get(self, user_id: str, reflection_id: str) -> dict[str, Any]:
        entry = self._reflections.find_by_id_for_user(reflection_id, user_id)
        if entry is None:
            raise NotFoundError("Reflection not found")
        return entry
