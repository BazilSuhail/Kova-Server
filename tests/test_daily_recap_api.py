"""Daily recap: the endpoint that always 500'd before the refactor."""
from __future__ import annotations

from datetime import UTC, datetime


def test_daily_recap_returns_200_with_expected_shape(client, auth):
    headers = auth()
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    done = client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Morning run", "dueDate": today},
    ).get_json()
    client.put(
        f"/api/tasks/{done['taskId']}", headers=headers, json={"isCompleted": True}
    )
    client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Write docs", "dueDate": today},
    )
    client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Far future", "dueDate": "2099-01-01"},
    )

    response = client.get("/api/daily-recap/", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"date", "completedTasks", "pendingTasks", "mood"}
    assert body["completedTasks"] == ["Morning run"]
    assert body["pendingTasks"] == ["Write docs"]
    assert body["mood"] == "Not recorded"


def test_daily_recap_reports_planner_reflection_as_mood(client, auth):
    headers = auth()
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    client.post("/api/planner/", headers=headers, json={"date": today, "reflection": "Focused"})

    body = client.get("/api/daily-recap/", headers=headers).get_json()
    assert body["mood"] == "Focused"


def test_daily_recap_returns_401_without_token(client):
    assert client.get("/api/daily-recap/").status_code == 401
