"""Task CRUD plus the two AI-assisted creation flows (natural language, voice)."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from ..core.exceptions import NotFoundError, ValidationError
from ..core.query import PageParams, page_payload
from ..repositories.subtask_repository import SubtaskRepository
from ..repositories.task_repository import TaskRepository
from ..utils.assemblyai_utils import transcribe_audio, upload_audio
from ..utils.categorization import categorize_locally
from ..utils.llm_utils import generate_task_fields_from_llm, generate_title_from_llm
from ..utils.ocr_utils import extract_text_from_image
from ..utils.title_utils import rewrite_title

# Whitelist for partial updates — clients cannot rewrite ids/ownership/timestamps.
_UPDATABLE_FIELDS = ("title", "description", "category", "dueDate", "isCompleted")


def _build_document(
    user_id: str, fields: dict[str, Any], created_from: str
) -> dict[str, Any]:
    """Shape a new task exactly as the legacy inline literals did."""
    return {
        "taskId": str(ObjectId()),
        "userId": user_id,
        "title": fields.get("title", ""),
        "description": fields.get("description", ""),
        "category": fields.get("category", ""),
        "dueDate": fields.get("dueDate", ""),
        "isCompleted": False,
        "createdFrom": created_from,
        "createdAt": datetime.now(UTC).isoformat(),
        "hasSubtasks": False,
    }


class TaskService:
    def __init__(
        self,
        tasks: TaskRepository,
        subtasks: SubtaskRepository,
        tombstones: object | None = None,
    ) -> None:
        self._tasks = tasks
        self._subtasks = subtasks
        self._tombstones = tombstones

    def create(self, data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Create a manual task (route already validated ``title`` presence)."""
        document = {
            "taskId": str(ObjectId()),
            "userId": user_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "category": data.get("category", ""),
            "dueDate": data.get("dueDate", ""),
            "isCompleted": False,
            "createdFrom": data.get("createdFrom", "manual"),
            "createdAt": datetime.now(UTC).isoformat(),
            "hasSubtasks": False,
        }
        return self._tasks.insert_task(document)

    def create_from_natural_language(self, user_id: str, prompt: str) -> dict[str, Any]:
        """Parse a free-text prompt through the LLM into a task.

        LLM failures surface as 400s because the legacy route caught
        ``ValueError`` and returned 400 — the prompt is the bad input there.
        """
        try:
            fields = generate_task_fields_from_llm(prompt)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return self._tasks.insert_task(
            _build_document(user_id, fields, "natural-language")
        )

    def create_from_voice(self, user_id: str, file_stream: Any) -> dict[str, Any]:
        """Upload audio → transcribe → LLM fields → task.

        Failures here bubble up as 500s, matching the legacy route which only
        caught ``Exception`` and returned 500 for every voice-flow error.
        """
        audio_url = upload_audio(file_stream)
        transcript = transcribe_audio(audio_url)
        fields = generate_task_fields_from_llm(transcript)
        return self._tasks.insert_task(_build_document(user_id, fields, "voice"))

    def create_from_image(
        self, user_id: str, file_stream: Any, filename: str = "upload.jpg"
    ) -> dict[str, Any]:
        """OCR an image (camera/scan) → LLM fields → task (feature 11).

        Both providers are required (OCR key + Groq key); a missing key surfaces
        as ``AIConfigError`` → 503, a malformed LLM reply as 400 (NLP contract).
        """
        text = extract_text_from_image(file_stream, filename=filename)
        try:
            fields = generate_task_fields_from_llm(text)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        task = self._tasks.insert_task(_build_document(user_id, fields, "image"))
        # ``extractedText`` is echoed for transparency but never persisted.
        return {**task, "extractedText": text}

    def categorize(self, user_id: str, task_id: str) -> str:
        """Re-derive a task's category locally and persist it (feature 4)."""
        task = self._tasks.find_for_user(task_id, user_id)
        if task is None:
            raise NotFoundError("Task not found")
        category = categorize_locally(
            task.get("title", ""), task.get("description", "")
        )
        self._tasks.update_fields(task_id, user_id, {"category": category})
        return category

    def suggest_title(self, title: str) -> str:
        """Rewrite a vague title into a clear one (feature 19).

        Falls back to the local heuristic when no Groq key is configured, so the
        endpoint always answers.
        """
        return rewrite_title(
            title, llm_callable=generate_title_from_llm, use_llm=True
        )

    def rewrite_task_title(self, user_id: str, task_id: str) -> str:
        """Rewrite and persist an existing task's title (feature 19)."""
        task = self._tasks.find_for_user(task_id, user_id)
        if task is None:
            raise NotFoundError("Task not found")
        new_title = self.suggest_title(task.get("title", ""))
        self._tasks.update_fields(task_id, user_id, {"title": new_title})
        return new_title

    def list(
        self,
        user_id: str,
        *,
        completed: bool | None = None,
        category: str | None = None,
        query: str | None = None,
        page: PageParams | None = None,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """List tasks, optionally filtered and/or paginated.

        No ``page`` → the legacy bare-array response (unfiltered: identical
        query to the original ``find_all``). With ``page`` → the paged envelope.
        """
        filters: dict[str, Any] = {"userId": user_id}
        if completed is not None:
            filters["isCompleted"] = completed
        if category:
            filters["category"] = category
        if query:
            filters["title"] = {"$regex": re.escape(query), "$options": "i"}
        if page is None:
            return self._tasks.find_many(filters)
        total = self._tasks.count(filters)
        items = self._tasks.find_page(filters, skip=page.skip, limit=page.limit)
        return page_payload(items, total, page)

    def get(self, task_id: str, user_id: str) -> dict[str, Any] | None:
        return self._tasks.find_for_user(task_id, user_id)

    def update(self, task_id: str, user_id: str, data: dict[str, Any]) -> bool:
        """Partial update; False means "not found" *or* "no fields actually changed"."""
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        return self._tasks.update_fields(task_id, user_id, fields) > 0

    def delete(self, task_id: str, user_id: str) -> bool:
        """Delete a task **and** its subtasks.

        The cascade was added in Sprint A — the legacy implementation left
        orphaned subtask documents behind. Only tasks owned by the caller are
        affected, and nothing happens when the task does not exist.
        """
        if self._tasks.delete(task_id, user_id) == 0:
            return False
        self._subtasks.delete_by_task(task_id)
        if self._tombstones is not None:
            self._tombstones.record(  # type: ignore[attr-defined]
                user_id, "tasks", task_id, datetime.now(UTC).isoformat()
            )
        return True
