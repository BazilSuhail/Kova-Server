"""Summary endpoints: upload validation, paging, and convert-to-task."""
from __future__ import annotations

import io


def _create_summary(client, headers, monkeypatch, filename="notes.pdf"):
    """Create one summary with the PDF reader and LLM stubbed (no network)."""
    monkeypatch.setattr(
        "app.api.summaries.extract_pdf_text", lambda _file: "Extracted text"
    )
    monkeypatch.setattr(
        "app.services.summary_service.generate_summary_from_llm",
        lambda _text: ["Bullet one", "Bullet two"],
    )
    response = client.post(
        "/api/summaries/create",
        headers=headers,
        data={"file": (io.BytesIO(b"%PDF-1.4 stub"), filename)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    return response.get_json()["summary"]["summaryId"]


def test_create_summary_returns_400_when_file_missing(client, auth):
    headers = auth()
    response = client.post("/api/summaries/create", headers=headers)
    assert response.status_code == 400
    assert response.get_json() == {"message": "PDF file is required"}


def test_list_summaries_returns_empty_for_new_user(client, auth):
    headers = auth()
    response = client.get("/api/summaries/", headers=headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_convert_summary_to_tasks_persists_companion_task(
    client, auth, monkeypatch
):
    headers = auth()
    summary_id = _create_summary(client, headers, monkeypatch)

    response = client.post(
        f"/api/summaries/{summary_id}/convert-to-tasks", headers=headers
    )
    assert response.status_code == 201
    task = response.get_json()
    assert task["title"] == "Summary Task"
    assert task["description"] == "Bullet one Bullet two"
    assert task["taskId"]

    # …and the task really exists in the task store.
    fetched = client.get(
        f"/api/tasks/{task['taskId']}", headers=headers
    )
    assert fetched.status_code == 200
    assert fetched.get_json()["title"] == "Summary Task"


def test_convert_summary_to_tasks_returns_404_when_missing(client, auth):
    headers = auth()
    response = client.post(
        "/api/summaries/689ffffffffffffffffffff/convert-to-tasks", headers=headers
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "Summary not found"}


def test_list_summaries_paging_returns_envelope(client, auth, monkeypatch):
    headers = auth()
    for index in range(3):
        _create_summary(client, headers, monkeypatch, filename=f"doc{index}.pdf")

    response = client.get("/api/summaries/?page=1&limit=2", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["totalPages"] == 2
