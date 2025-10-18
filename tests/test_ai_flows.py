"""Sprint D: AI-flow error semantics and Groq client behaviour.

Every test is offline: provider calls are stubbed at the transport or service
layer, and the no-key paths guard before any network I/O.
"""
from __future__ import annotations

import dataclasses
import io
import json

import pytest
import requests
from app import create_app
from app.config import Settings

from tests.support.fake_mongo import FakeMongoClient


class _FakeResponse:
    """Minimal stand-in for a successful Groq chat-completions response."""

    def __init__(self, content: str) -> None:
        self._content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def _stub_groq(monkeypatch, content: str, captured: dict | None = None) -> None:
    """Replace the Groq transport with a canned assistant message."""

    def _post(url, json=None, headers=None, timeout=None):
        if captured is not None:
            captured.update(url=url, payload=json, headers=headers, timeout=timeout)
        return _FakeResponse(content)

    monkeypatch.setattr("app.utils.groq_client.requests.post", _post)


def _explode(*_args, **_kwargs):
    raise requests.exceptions.ConnectionError("provider down")


# --- NLP task flow ---------------------------------------------------------


def test_nlp_task_returns_400_when_llm_transport_fails(app, client, auth, monkeypatch):
    app.config["GROQ_API_KEY"] = "test-key"
    monkeypatch.setattr("app.utils.groq_client.requests.post", _explode)
    response = client.post(
        "/api/tasks/create/natural-language",
        headers=auth(),
        json={"prompt": "buy milk tomorrow"},
    )
    assert response.status_code == 400  # legacy contract: bad-prompt path
    assert response.get_json()["message"].startswith("API request failed")


def test_nlp_task_returns_503_when_groq_key_missing(client, auth):
    # for_testing() ships without keys → the guard fires before any network.
    response = client.post(
        "/api/tasks/create/natural-language",
        headers=auth(),
        json={"prompt": "buy milk tomorrow"},
    )
    assert response.status_code == 503
    assert response.get_json() == {"message": "AI provider is not configured"}


def test_nlp_task_created_from_stubbed_llm(app, client, auth, monkeypatch):
    app.config["GROQ_API_KEY"] = "test-key"
    _stub_groq(
        monkeypatch,
        json.dumps(
            {
                "title": "Buy milk",
                "description": "Buy milk from the store before it closes.",
                "category": "personal",
                "dueDate": "2026-10-06",
                "createdFrom": "auto",
            }
        ),
    )
    response = client.post(
        "/api/tasks/create/natural-language",
        headers=auth(),
        json={"prompt": "buy milk tomorrow"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Buy milk"
    assert body["createdFrom"] == "natural-language"


# --- Voice flow ------------------------------------------------------------


def test_voice_task_returns_503_when_assemblyai_key_missing(client, auth):
    response = client.post(
        "/api/tasks/create/voice",
        headers=auth(),
        data={"file": (io.BytesIO(b"RIFF0000WAVE"), "clip.wav")},
    )
    assert response.status_code == 503
    assert response.get_json() == {"message": "AI provider is not configured"}


def test_voice_task_returns_500_when_upload_fails(monkeypatch):
    # Legacy contract: every voice-flow failure answered 500.
    settings = dataclasses.replace(
        Settings.for_testing(), assemblyai_api_key="test-key"
    )
    application = create_app(settings=settings, mongo_client=FakeMongoClient())
    application.config["TESTING"] = True
    application.config["PROPAGATE_EXCEPTIONS"] = False
    client = application.test_client()
    token = client.post(
        "/api/auth/signup",
        json={
            "name": "Ada",
            "email": "ada@example.com",
            "password": "pw123456",
        },
    ).get_json()["access_token"]
    monkeypatch.setattr("app.utils.assemblyai_utils.requests.post", _explode)

    response = client.post(
        "/api/tasks/create/voice",
        headers={"Authorization": f"Bearer {token}"},
        data={"file": (io.BytesIO(b"RIFF0000WAVE"), "clip.wav")},
    )
    assert response.status_code == 500
    assert response.get_json() == {"message": "Internal server error"}


# --- Summary flow ----------------------------------------------------------


def test_summary_returns_503_when_groq_key_missing(client, auth, monkeypatch):
    monkeypatch.setattr(
        "app.api.summaries.extract_pdf_text", lambda _file: "Extracted text"
    )
    response = client.post(
        "/api/summaries/create",
        headers=auth(),
        data={"file": (io.BytesIO(b"%PDF-1.4 stub"), "notes.pdf")},
    )
    assert response.status_code == 503
    assert response.get_json() == {"message": "AI provider is not configured"}


def test_summary_returns_500_when_llm_transport_fails(app, client, auth, monkeypatch):
    # Legacy contract: summary LLM failures answered 500.
    app.config["GROQ_API_KEY"] = "test-key"
    monkeypatch.setattr(
        "app.api.summaries.extract_pdf_text", lambda _file: "Extracted text"
    )
    monkeypatch.setattr("app.utils.groq_client.requests.post", _explode)

    response = client.post(
        "/api/summaries/create",
        headers=auth(),
        data={"file": (io.BytesIO(b"%PDF-1.4 stub"), "notes.pdf")},
    )
    assert response.status_code == 500
    assert response.get_json() == {"message": "Internal server error"}


# --- Subtask flow (tracked 404 → 502 fix) ---------------------------------


def test_subtasks_return_502_when_llm_fails(client, auth, monkeypatch):
    def _boom(_description):
        raise ValueError("Failed to parse LLM response: broken")

    monkeypatch.setattr(
        "app.services.subtask_service.generate_subtasks_from_description", _boom
    )
    headers = auth()
    task = client.post(
        "/api/tasks/", headers=headers, json={"title": "Big project"}
    ).get_json()

    response = client.post(
        "/api/subtasks/create", headers=headers, json={"taskId": task["taskId"]}
    )
    assert response.status_code == 502
    assert response.get_json() == {"message": "Subtask generation failed"}


def test_subtasks_return_503_when_groq_key_missing(client, auth):
    # No stub: the real generator guards on the key before any network I/O,
    # and AIConfigError flows past the ValueError handler → 503.
    headers = auth()
    task = client.post(
        "/api/tasks/", headers=headers, json={"title": "Big project"}
    ).get_json()

    response = client.post(
        "/api/subtasks/create", headers=headers, json={"taskId": task["taskId"]}
    )
    assert response.status_code == 503
    assert response.get_json() == {"message": "AI provider is not configured"}


# --- Transport configuration ----------------------------------------------


def test_groq_payload_uses_configured_model_and_timeout(app, monkeypatch):
    app.config["GROQ_API_KEY"] = "test-key"
    captured: dict = {}
    _stub_groq(monkeypatch, "hello", captured)

    from app.utils.groq_client import chat_completion

    with app.app_context():
        out = chat_completion(
            system_prompt="sys", user_content="user", max_tokens=10, temperature=0.1
        )

    assert out == "hello"
    assert captured["payload"]["model"] == app.config["GROQ_MODEL"]
    assert captured["timeout"] == app.config["LLM_TIMEOUT_SECONDS"]
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["payload"]["messages"][0]["content"] == "sys"


# --- Response parsing rules (unit-level) -----------------------------------


def _generate(fn, app, monkeypatch, content: str):
    app.config["GROQ_API_KEY"] = "test-key"
    _stub_groq(monkeypatch, content)
    with app.app_context():
        return fn()


def test_subtask_generator_truncates_overdelivery(app, monkeypatch):
    from app.utils.sub_tasks_utils import generate_subtasks_from_description

    items = [f"step {i}" for i in range(10)]
    result = _generate(
        lambda: generate_subtasks_from_description("desc"),
        app,
        monkeypatch,
        json.dumps(items),
    )
    assert result == items[:8]  # prompt promises 3–8; first 8 kept in order


def test_subtask_generator_rejects_too_few_items(app, monkeypatch):
    from app.utils.sub_tasks_utils import generate_subtasks_from_description

    with pytest.raises(ValueError, match="between 3 and 8"):
        _generate(
            lambda: generate_subtasks_from_description("desc"),
            app,
            monkeypatch,
            json.dumps(["one", "two"]),
        )


def test_subtask_generator_rejects_non_array_answer(app, monkeypatch):
    from app.utils.sub_tasks_utils import generate_subtasks_from_description

    with pytest.raises(ValueError, match="not a valid list"):
        _generate(
            lambda: generate_subtasks_from_description("desc"),
            app,
            monkeypatch,
            '"just a string"',
        )


def test_task_fields_reject_non_string_title(app, monkeypatch):
    from app.utils.llm_utils import generate_task_fields_from_llm

    payload = {
        "title": 3,
        "description": "d",
        "category": "c",
        "dueDate": "2026-10-06",
        "createdFrom": "auto",
    }
    with pytest.raises(ValueError, match="'title' is not a string"):
        _generate(
            lambda: generate_task_fields_from_llm("prompt"),
            app,
            monkeypatch,
            json.dumps(payload),
        )


def test_task_fields_reject_missing_fields(app, monkeypatch):
    from app.utils.llm_utils import generate_task_fields_from_llm

    with pytest.raises(ValueError, match="missing required fields"):
        _generate(
            lambda: generate_task_fields_from_llm("prompt"),
            app,
            monkeypatch,
            json.dumps({"title": "only one"}),
        )


def test_summary_rejects_bullet_count_out_of_range(app, monkeypatch):
    from app.utils.summary_utils import generate_summary_from_llm

    with pytest.raises(ValueError, match="between 4 and 9"):
        _generate(
            lambda: generate_summary_from_llm("text"),
            app,
            monkeypatch,
            json.dumps(["a", "b", "c"]),
        )
