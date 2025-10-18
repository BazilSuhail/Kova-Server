"""Calendar day/week/month views (feature 5)."""
from __future__ import annotations


def test_calendar_week_has_seven_days_and_buckets_tasks(client, auth):
    headers = auth()
    client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Midweek", "dueDate": "2026-10-07"},
    )
    client.post("/api/planner/", headers=headers, json={"date": "2026-10-05"})

    body = client.get(
        "/api/calendar/?view=week&date=2026-10-05", headers=headers
    ).get_json()
    assert body["view"] == "week"
    assert body["start"] == "2026-10-05"  # Monday
    assert body["end"] == "2026-10-11"
    assert len(body["days"]) == 7

    wednesday = next(d for d in body["days"] if d["date"] == "2026-10-07")
    assert [t["title"] for t in wednesday["tasks"]] == ["Midweek"]
    monday = next(d for d in body["days"] if d["date"] == "2026-10-05")
    assert monday["planner"]["date"] == "2026-10-05"


def test_calendar_day_view_is_single_day(client, auth):
    body = client.get(
        "/api/calendar/?view=day&date=2026-10-07", headers=auth()
    ).get_json()
    assert len(body["days"]) == 1
    assert body["days"][0]["date"] == "2026-10-07"


def test_calendar_month_view_covers_the_month(client, auth):
    body = client.get(
        "/api/calendar/?view=month&date=2026-02-15", headers=auth()
    ).get_json()
    assert body["start"] == "2026-02-01"
    assert body["end"] == "2026-02-28"
    assert len(body["days"]) == 28


def test_calendar_rejects_unknown_view(client, auth):
    response = client.get("/api/calendar/?view=decade", headers=auth())
    assert response.status_code == 400
    assert response.get_json() == {"message": "view must be one of: day, week, month"}


def test_calendar_rejects_bad_date(client, auth):
    response = client.get("/api/calendar/?date=not-a-date", headers=auth())
    assert response.status_code == 400
