"""Notification endpoints: creation validation, feed ordering, read updates."""
from __future__ import annotations


def _create(client, headers, title, message="Body"):
    return client.post(
        "/api/notifications/",
        headers=headers,
        json={"title": title, "message": message},
    )


def test_create_notification_returns_201_with_unread_state(client, auth):
    headers = auth()
    response = _create(client, headers, "Task due")
    assert response.status_code == 201
    body = response.get_json()
    assert body["title"] == "Task due"
    assert body["read"] is False
    assert body["notificationId"]


def test_create_notification_returns_400_when_fields_missing(client, auth):
    headers = auth()
    response = client.post(
        "/api/notifications/", headers=headers, json={"title": "Only a title"}
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "Title and message are required"}


def test_list_notifications_returns_newest_first(client, auth):
    headers = auth()
    _create(client, headers, "First")
    _create(client, headers, "Second")
    listing = client.get("/api/notifications/", headers=headers)
    assert listing.status_code == 200
    titles = [item["title"] for item in listing.get_json()]
    assert titles == ["Second", "First"]


def test_update_notification_returns_200_when_marking_read(client, auth):
    headers = auth()
    created = _create(client, headers, "Read me").get_json()
    response = client.put(
        f"/api/notifications/{created['notificationId']}",
        headers=headers,
        json={"read": True},
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Notification updated"}


def test_update_notification_returns_404_when_missing(client, auth):
    headers = auth()
    response = client.put(
        "/api/notifications/689ffffffffffffffffffff",
        headers=headers,
        json={"read": True},
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "Notification not found"}
