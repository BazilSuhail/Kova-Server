"""Life-assistant features: categorisation, titles, notes, OCR, settings."""
from __future__ import annotations

import io

import app.services.summary_service as summary_module
import app.services.task_service as task_module
import app.utils.ocr_utils as ocr_module

# --- feature 4: smart categorisation ---------------------------------------


def test_manual_task_is_auto_categorised(client, auth):
    body = client.post(
        "/api/tasks/", headers=auth(), json={"title": "Study for the exam"}
    ).get_json()
    assert body["category"] == "academics"


def test_explicit_category_is_preserved(client, auth):
    body = client.post(
        "/api/tasks/",
        headers=auth(),
        json={"title": "Anything", "category": "custom"},
    ).get_json()
    assert body["category"] == "custom"


def test_recategorize_endpoint_updates_stored_category(client, auth):
    headers = auth()
    task = client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Pay the electricity bill", "category": "other"},
    ).get_json()

    response = client.post(f"/api/tasks/{task['taskId']}/categorize", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["category"] == "finance"
    assert (
        client.get(f"/api/tasks/{task['taskId']}", headers=headers).get_json()["category"]
        == "finance"
    )


# --- feature 19: smart event title generator -------------------------------


def test_suggest_title_expands_abbreviations(client, auth):
    body = client.post(
        "/api/tasks/suggest-title", headers=auth(), json={"title": "buy milk tmrw"}
    ).get_json()
    assert body["title"] == "Buy milk tomorrow"


def test_rewrite_task_title_persists(client, auth):
    headers = auth()
    task = client.post(
        "/api/tasks/", headers=headers, json={"title": "call mom tmrw"}
    ).get_json()

    response = client.post(
        f"/api/tasks/{task['taskId']}/rewrite-title", headers=headers
    )
    assert response.get_json()["title"] == "Call mom tomorrow"
    assert (
        client.get(f"/api/tasks/{task['taskId']}", headers=headers).get_json()["title"]
        == "Call mom tomorrow"
    )


# --- feature 8: auto notes summarizer (3-5 bullets) ------------------------


def test_create_summary_from_text_uses_notes_path(client, auth, monkeypatch):
    monkeypatch.setattr(
        summary_module,
        "generate_notes_summary_from_llm",
        lambda _text: ["One", "Two", "Three"],
    )
    response = client.post(
        "/api/summaries/create-from-text",
        headers=auth(),
        json={"text": "A long lecture transcript", "title": "Lecture 3"},
    )
    assert response.status_code == 201
    summary = response.get_json()["summary"]
    assert summary["sourceType"] == "note"
    assert summary["summaryBullets"] == ["One", "Two", "Three"]
    assert summary["originalFileName"] == "Lecture 3"


def test_create_summary_from_text_requires_text(client, auth):
    response = client.post("/api/summaries/create-from-text", headers=auth(), json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "text is required"}


# --- feature 11: quick add from camera / OCR -------------------------------


def test_create_task_from_image_uses_ocr_and_llm(client, auth, monkeypatch):
    monkeypatch.setattr(
        task_module,
        "extract_text_from_image",
        lambda _stream, filename="": "Buy milk tomorrow",
    )
    monkeypatch.setattr(
        task_module,
        "generate_task_fields_from_llm",
        lambda _text: {
            "title": "Buy milk",
            "description": "Buy milk from the store.",
            "category": "errands",
            "dueDate": "2026-10-18",
            "createdFrom": "auto",
        },
    )
    response = client.post(
        "/api/tasks/create/image",
        headers=auth(),
        data={"file": (io.BytesIO(b"jpegbytes"), "note.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["createdFrom"] == "image"
    assert body["extractedText"] == "Buy milk tomorrow"


def test_create_task_from_image_requires_a_file(client, auth):
    response = client.post("/api/tasks/create/image", headers=auth())
    assert response.status_code == 400
    assert response.get_json() == {"message": "Image file is required."}


def test_create_task_from_image_503_when_ocr_key_missing(client, auth):
    response = client.post(
        "/api/tasks/create/image",
        headers=auth(),
        data={"file": (io.BytesIO(b"jpegbytes"), "note.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 503
    assert response.get_json() == {"message": "OCR provider is not configured"}


def test_create_task_from_image_rejects_image_over_1mb(client, auth, app):
    app.config["OCR_API_KEY"] = "test-key"
    response = client.post(
        "/api/tasks/create/image",
        headers=auth(),
        data={"file": (io.BytesIO(b"x" * (1024 * 1024 + 1)), "big.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "Image must be 1 MB or smaller."}


class _FakeOcrSpaceResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b""
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_ocr_utils_calls_ocr_space_with_key_and_file(app, monkeypatch):
    app.config["OCR_API_KEY"] = "test-key"
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return _FakeOcrSpaceResponse(
            {"IsErroredOnProcessing": False, "ParsedResults": [{"ParsedText": "Buy milk\n"}]}
        )

    monkeypatch.setattr(ocr_module.requests, "post", fake_post)
    with app.app_context():
        text = ocr_module.extract_text_from_image(
            io.BytesIO(b"image-bytes"), filename="note.png"
        )

    assert text == "Buy milk"
    assert captured["url"].endswith("/parse/image")
    assert captured["data"]["apikey"] == "test-key"
    assert captured["data"]["language"] == "eng"
    files = captured["files"]
    assert "filename" in files
    sent_filename, sent_content = files["filename"]
    assert sent_filename == "note.png"
    assert sent_content == b"image-bytes"


# --- feature 15: customisation settings ------------------------------------


def test_settings_roundtrip_ignores_unknown_keys(client, auth):
    headers = auth()
    initial = client.get("/api/users/profile/settings", headers=headers).get_json()
    assert initial["theme"] == "light"

    updated = client.put(
        "/api/users/profile/settings",
        headers=headers,
        json={"theme": "dark", "fontSize": "large", "bogus": "ignored"},
    ).get_json()
    assert updated["theme"] == "dark"
    assert updated["fontSize"] == "large"
    assert "bogus" not in updated
