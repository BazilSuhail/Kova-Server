"""Smart reminders: scheduling, validation, and delivery (feature 10)."""
from __future__ import annotations

import app.services.reminder_service as reminder_module


def test_create_reminder_returns_201_and_normalises_date(client, auth):
    response = client.post(
        "/api/reminders/",
        headers=auth(),
        json={"title": "Stand up", "fireAt": "2026-10-20"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "pending"
    assert body["fireAt"].startswith("2026-10-20T09:00:00")


def test_create_reminder_requires_title_and_fire_at(client, auth):
    response = client.post("/api/reminders/", headers=auth(), json={"title": "x"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "title and fireAt are required"}


def test_create_reminder_rejects_bad_datetime(client, auth):
    response = client.post(
        "/api/reminders/",
        headers=auth(),
        json={"title": "x", "fireAt": "not-a-date"},
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "fireAt must be an ISO date or datetime"}


def test_list_and_delete_reminder(client, auth):
    headers = auth()
    created = client.post(
        "/api/reminders/",
        headers=headers,
        json={"title": "Later", "fireAt": "2030-01-01T00:00:00+00:00"},
    ).get_json()
    assert len(client.get("/api/reminders/", headers=headers).get_json()) == 1

    deleted = client.delete(f"/api/reminders/{created['reminderId']}", headers=headers)
    assert deleted.get_json() == {"message": "Reminder deleted"}
    assert client.get("/api/reminders/", headers=headers).get_json() == []


def test_due_reminder_creates_notification_and_is_marked_sent(app, client, auth):
    headers = auth()
    client.post(
        "/api/reminders/",
        headers=headers,
        json={"title": "Pay rent", "message": "due now", "fireAt": "2000-01-01T00:00:00+00:00"},
    )

    with app.app_context():
        fired = app.extensions["zenflow.services"].reminders.deliver_due()

    assert fired == 1
    notifications = client.get("/api/notifications/", headers=headers).get_json()
    assert any(n["title"] == "Pay rent" for n in notifications)
    assert len(client.get("/api/reminders/?status=sent", headers=headers).get_json()) == 1


def test_delivery_pushes_to_registered_devices(app, client, auth, monkeypatch):
    headers = auth()
    calls: list[list[dict]] = []

    def _capture(messages):
        calls.append(messages)
        return ["ExponentPushToken[stale]"]

    monkeypatch.setattr(reminder_module, "send_push", _capture)

    client.post(
        "/api/devices/",
        headers=headers,
        json={"expoPushToken": "ExponentPushToken[stale]", "platform": "ios"},
    )
    client.post(
        "/api/reminders/",
        headers=headers,
        json={"title": "Nudge", "fireAt": "2000-01-01T00:00:00+00:00"},
    )

    with app.app_context():
        app.extensions["zenflow.services"].reminders.deliver_due()

    assert calls and calls[0][0]["to"] == "ExponentPushToken[stale]"
    # A token Expo reports as dead is pruned.
    assert client.get("/api/devices/", headers=headers).get_json() == []
