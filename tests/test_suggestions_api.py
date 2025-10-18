"""Adaptive suggestions engine (feature 17)."""
from __future__ import annotations


def test_suggestions_are_empty_for_a_quiet_new_user(client, auth):
    body = client.get("/api/suggestions/", headers=auth()).get_json()
    # Only the "log your mood" nudge is expected with no data.
    ids = {s["id"] for s in body["suggestions"]}
    assert ids == {"log_mood"}


def test_suggestions_flag_overdue_tasks(client, auth):
    headers = auth()
    client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Old chore", "dueDate": "2000-01-01"},
    )
    body = client.get("/api/suggestions/", headers=headers).get_json()
    ids = {s["id"] for s in body["suggestions"]}
    assert "reschedule_overdue" in ids


def test_suggestions_encourage_when_completion_is_high(client, auth):
    headers = auth()
    task = client.post("/api/tasks/", headers=headers, json={"title": "Done"}).get_json()
    client.put(
        f"/api/tasks/{task['taskId']}", headers=headers, json={"isCompleted": True}
    )
    body = client.get("/api/suggestions/", headers=headers).get_json()
    ids = {s["id"] for s in body["suggestions"]}
    assert "momentum" in ids


def test_suggestions_require_auth(client):
    assert client.get("/api/suggestions/").status_code == 401
