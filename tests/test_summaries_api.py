"""Summary endpoints: upload validation (LLM paths are covered by TODO, not tests)."""
from __future__ import annotations


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
