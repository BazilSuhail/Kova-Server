"""PDF → LLM bullet summary, plus a derived task suggestion."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from ..repositories.summary_repository import SummaryRepository
from ..utils.summary_utils import generate_summary_from_llm

# Whitelist for partial updates.
_UPDATABLE_FIELDS = ("sourceType", "originalFileName", "summaryBullets")


class SummaryService:
    def __init__(self, summaries: SummaryRepository) -> None:
        self._summaries = summaries

    def create(
        self, user_id: str, extracted_text: str, original_filename: str
    ) -> dict[str, Any]:
        """Summarize extracted PDF text and persist the summary.

        LLM failures are allowed to bubble (legacy returned 500 for them).
        The companion ``task`` is returned but *not* persisted — exactly what
        the legacy code did; persisting it is tracked in docs/TODO.md.
        """
        summary_bullets = generate_summary_from_llm(extracted_text)
        task = {
            "taskId": str(ObjectId()),
            "userId": user_id,
            "title": "Summary Task",
            "description": " ".join(summary_bullets),
            "category": "Uncategorized",
            "dueDate": "",
            "isCompleted": False,
            "createdFrom": "natural-language",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        summary = {
            "summaryId": str(ObjectId()),
            "userId": user_id,
            "sourceType": "pdf",
            "originalFileName": original_filename,
            "summaryBullets": summary_bullets,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        self._summaries.insert(summary)
        return {"summary": summary, "task": task}

    def list(self, user_id: str) -> list[dict[str, Any]]:
        return self._summaries.find_for_user(user_id)

    def update(self, summary_id: str, user_id: str, data: dict[str, Any]) -> bool:
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        return self._summaries.update_fields(summary_id, user_id, fields) > 0

    def delete(self, summary_id: str, user_id: str) -> bool:
        return self._summaries.delete(summary_id, user_id) > 0
