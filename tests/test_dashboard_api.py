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
    "todayProgress",
    "weeklyCompletion",
    "moodTrend",
    "recentSummaries",
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


def test_dashboard_home_chart_fields(client, auth):
    from datetime import UTC, datetime

    headers = auth()
    today = datetime.now(UTC).date().isoformat()
    created = client.post(
        "/api/tasks/", headers=headers, json={"title": "Done", "dueDate": today}
    ).get_json()
    client.post("/api/tasks/", headers=headers, json={"title": "Open", "dueDate": today})
    client.put(f"/api/tasks/{created['taskId']}", headers=headers, json={"isCompleted": True})
    client.post("/api/mood/", headers=headers, json={"mood": "good"})

    body = client.get("/api/dashboard/", headers=headers).get_json()
    assert body["todayProgress"] == {"total": 2, "completed": 1, "pending": 1}
    assert len(body["weeklyCompletion"]) == 7
    assert body["weeklyCompletion"][-1] == {"date": today, "completed": 1, "total": 2}
    assert len(body["moodTrend"]) == 7
    assert body["moodTrend"][-1]["entries"] == 1
    assert body["recentSummaries"] == []
