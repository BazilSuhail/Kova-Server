"""Weekly recap: rolling 7-day window shape, validation, and auth."""
from __future__ import annotations

from datetime import datetime, timezone


def test_weekly_recap_returns_seven_days_ending_today(client, auth):
    headers = auth()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Due today", "dueDate": today},
    )

    response = client.get("/api/weekly-recap/", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert body["endDate"] == today
    assert len(body["days"]) == 7
    # startDate is 6 days before endDate (inclusive window).
    start = datetime.strptime(body["startDate"], "%Y-%m-%d")
    end = datetime.strptime(body["endDate"], "%Y-%m-%d")
    assert (end - start).days == 6
    assert set(body["totals"]) == {"completedTasks", "pendingTasks"}
    assert body["totals"]["pendingTasks"] == 1
    today_entry = next(d for d in body["days"] if d["date"] == today)
    assert today_entry["pendingTasks"] == ["Due today"]
    assert set(today_entry) == {"date", "completedTasks", "pendingTasks", "mood"}


def test_weekly_recap_accepts_explicit_end_date(client, auth):
    headers = auth()
    response = client.get(
        "/api/weekly-recap/?end=2026-01-07", headers=headers
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["startDate"] == "2026-01-01"
    assert body["endDate"] == "2026-01-07"


def test_weekly_recap_rejects_malformed_end_date(client, auth):
    headers = auth()
    response = client.get("/api/weekly-recap/?end=yesterday", headers=headers)
    assert response.status_code == 400
    assert response.get_json()["message"] == "end must be a YYYY-MM-DD date"


def test_weekly_recap_requires_token(client):
    assert client.get("/api/weekly-recap/").status_code == 401
