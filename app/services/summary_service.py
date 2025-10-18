"""PDF → LLM bullet summary, plus a derived task suggestion."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from ..core.query import PageParams, page_payload
from ..repositories.summary_repository import SummaryRepository
from ..repositories.task_repository import TaskRepository
from ..utils.summary_utils import (
    generate_notes_summary_from_llm,
    generate_summary_from_llm,
)

# Whitelist for partial updates.
_UPDATABLE_FIELDS = ("sourceType", "originalFileName", "summaryBullets")


class SummaryService:
    def __init__(
        self,
        summaries: SummaryRepository,
        tasks: TaskRepository,
        tombstones: object | None = None,
    ) -> None:
        self._summaries = summaries
        self._tasks = tasks
        self._tombstones = tombstones

    def create(
        self, user_id: str, extracted_text: str, original_filename: str | None
    ) -> dict[str, Any]:
        """Summarize extracted PDF text and persist the summary.

        LLM failures are allowed to bubble (legacy returned 500 for them).
        The companion ``task`` is returned but *not* persisted — exactly what
        the legacy code did; clients persist it via
        ``POST /api/summaries/<id>/convert-to-tasks``.
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
            "created_at": datetime.now(UTC).isoformat(),
        }
        summary = {
            "summaryId": str(ObjectId()),
            "userId": user_id,
            "sourceType": "pdf",
            "originalFileName": original_filename,
            "summaryBullets": summary_bullets,
            "createdAt": datetime.now(UTC).isoformat(),
        }
        self._summaries.insert(summary)
        return {"summary": summary, "task": task}

    def create_from_text(
        self, user_id: str, text: str, title: str | None = None
    ) -> dict[str, Any]:
        """Summarize raw note text into 3-5 bullets (feature 8 — notes path).

        Unlike the PDF flow this never fabricates a task suggestion; notes are
        summarized standalone (persist a task later via convert-to-tasks, which
        works on any summary).
        """
        summary_bullets = generate_notes_summary_from_llm(text)
        summary = {
            "summaryId": str(ObjectId()),
            "userId": user_id,
            "sourceType": "note",
            "originalFileName": title or "",
            "summaryBullets": summary_bullets,
            "createdAt": datetime.now(UTC).isoformat(),
        }
        self._summaries.insert(summary)
        return {"summary": summary}

    def list(
        self, user_id: str, *, page: PageParams | None = None
    ) -> list[dict[str, Any]] | dict[str, Any]:
        if page is None:
            return self._summaries.find_for_user(user_id)
        total = self._summaries.count_for_user(user_id)
        items = self._summaries.find_page_for_user(
            user_id, skip=page.skip, limit=page.limit
        )
        return page_payload(items, total, page)

    def convert_to_task(
        self, summary_id: str, user_id: str
    ) -> dict[str, Any] | None:
        """Persist the companion task the create response only suggested.

        The task mirrors the legacy suggestion (same title/category/origin) so
        anything already displaying those suggestions keeps rendering the same
        document — it just exists in ``tasks`` now.
        """
        summary = self._summaries.find_by_id_for_user(summary_id, user_id)
        if summary is None:
            return None
        document = {
            "taskId": str(ObjectId()),
            "userId": user_id,
            "title": "Summary Task",
            "description": " ".join(summary.get("summaryBullets", [])),
            "category": "Uncategorized",
            "dueDate": "",
            "isCompleted": False,
            "createdFrom": "natural-language",
            "createdAt": datetime.now(UTC).isoformat(),
            "hasSubtasks": False,
        }
        return self._tasks.insert_task(document)

    def update(self, summary_id: str, user_id: str, data: dict[str, Any]) -> bool:
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        return self._summaries.update_fields(summary_id, user_id, fields) > 0

    def delete(self, summary_id: str, user_id: str) -> bool:
        deleted = self._summaries.delete(summary_id, user_id) > 0
        if deleted and self._tombstones is not None:
            self._tombstones.record(  # type: ignore[attr-defined]
                user_id, "summaries", summary_id, datetime.now(UTC).isoformat()
            )
        return deleted
