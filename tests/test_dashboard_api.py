"""Dashboard aggregation endpoint (feature 2)."""
from __future__ import annotations

EXPECTED_KEYS = {
    "date",
    "tasks",
    "todayTasks",
    "unreadNotifications",
    "nextReminders",
    "latestMood",
    "latestSummary",
    "streak",
    "suggestions",
}


def test_dashboard_requires_auth(client):
    assert client.get("/api/dashboard/").status_code == 401


def test_dashboard_aggregates_the_home_screen(client, auth):
    headers = auth()
    client.post("/api/tasks/", headers=headers, json={"title": "Buy milk"})
    client.post("/api/mood/", headers=headers, json={"mood": "good"})
    client.post(
        "/api/notifications/",
        headers=headers,
        json={"title": "Hi", "message": "there"},
    )

    response = client.get("/api/dashboard/", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == EXPECTED_KEYS
    assert body["tasks"]["total"] == 1
    assert body["tasks"]["pending"] == 1
    assert body["unreadNotifications"] == 1
    assert body["latestMood"]["mood"] == "good"
    assert isinstance(body["suggestions"], list)


def test_dashboard_is_empty_but_valid_for_new_user(client, auth):
    body = client.get("/api/dashboard/", headers=auth()).get_json()
    assert body["tasks"]["total"] == 0
    assert body["todayTasks"] == []
    assert body["latestMood"] is None
    assert body["latestSummary"] is None
