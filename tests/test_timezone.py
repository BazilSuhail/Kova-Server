"""Caller timezone (``X-Timezone``) drives "today" and day boundaries."""
from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.core.timezone import local_now, request_tz

# UTC+14 and UTC-11: their calendar dates always differ (25h apart).
AHEAD = "Pacific/Kiritimati"
BEHIND = "Pacific/Pago_Pago"


def _today(zone: str) -> str:
    return datetime.now(ZoneInfo(zone)).date().isoformat()


def test_request_tz_validates_and_falls_back_to_utc(app):
    for header, expected in (
        (AHEAD, ZoneInfo(AHEAD)),
        ("Not/A_Zone", UTC),
        ("../../etc/passwd", UTC),
        ("", UTC),
    ):
        with app.test_request_context(headers={"X-Timezone": header}):
            assert request_tz() == expected
    with app.app_context():  # no request → UTC
        assert local_now().utcoffset().total_seconds() == 0


def test_dashboard_today_follows_the_callers_zone(client, auth):
    headers = auth()
    client.post(
        "/api/tasks/", headers=headers,
        json={"title": "Ahead task", "dueDate": f"{_today(AHEAD)}T10:00:00"},
    )

    ahead = client.get("/api/dashboard/", headers={**headers, "X-Timezone": AHEAD})
    body = ahead.get_json()
    assert body["date"].startswith(_today(AHEAD))
    assert body["tasks"]["dueToday"] == 1
    assert body["weeklyCompletion"][-1]["date"] == _today(AHEAD)

    behind = client.get("/api/dashboard/", headers={**headers, "X-Timezone": BEHIND})
    assert behind.get_json()["tasks"]["dueToday"] == 0


def test_mood_date_and_trends_use_local_day(client, auth):
    headers = {**auth(), "X-Timezone": AHEAD}
    created = client.post("/api/mood/", headers=headers, json={"mood": "good"})
    assert created.get_json()["date"] == _today(AHEAD)

    trends = client.get("/api/mood/trends?days=7", headers=headers).get_json()
    assert trends["range"]["end"] == _today(AHEAD)
    assert trends["series"][-1]["entries"] == 1
    assert trends["streak"] == 1


def test_recaps_calendar_and_reflection_use_local_day(client, auth):
    headers = {**auth(), "X-Timezone": BEHIND}
    today = _today(BEHIND)
    assert client.get("/api/daily-recap/", headers=headers).get_json()["date"].startswith(today)
    assert client.get("/api/weekly-recap/", headers=headers).get_json()["endDate"] == today
    calendar = client.get("/api/calendar/?view=day", headers=headers).get_json()
    assert calendar["days"][0]["date"] == today
    assert client.get("/api/reflections/today", headers=headers).get_json()["date"] == today


def test_date_only_reminder_fires_at_9am_local(client, auth):
    headers = {**auth(), "X-Timezone": "Asia/Karachi"}  # UTC+5, no DST
    response = client.post(
        "/api/reminders/", headers=headers,
        json={"title": "Call mom", "fireAt": "2030-01-15"},
    )
    assert response.status_code == 201
    assert response.get_json()["fireAt"] == "2030-01-15T04:00:00+00:00"


def test_cors_preflight_allows_the_timezone_header(client):
    response = client.options(
        "/api/dashboard/",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, X-Timezone",
        },
    )
    allowed = response.headers.get("Access-Control-Allow-Headers", "").lower()
    assert "x-timezone" in allowed
