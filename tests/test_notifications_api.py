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


def test_get_notification_returns_single_item(client, auth):
    headers = auth()
    created = _create(client, headers, "Solo notice").get_json()
    response = client.get(
        f"/api/notifications/{created['notificationId']}", headers=headers
    )
    assert response.status_code == 200
    assert response.get_json()["title"] == "Solo notice"


def test_get_notification_returns_404_for_other_users_item(client, auth):
    mine = auth("owner@example.com")
    theirs = auth("other@example.com")
    created = _create(client, theirs, "Not yours").get_json()
    response = client.get(
        f"/api/notifications/{created['notificationId']}", headers=mine
    )
    assert response.status_code == 404


def test_delete_notification_removes_it_then_404s(client, auth):
    headers = auth()
    created = _create(client, headers, "Temp").get_json()
    notification_id = created["notificationId"]

    deleted = client.delete(
        f"/api/notifications/{notification_id}", headers=headers
    )
    assert deleted.status_code == 200
    assert deleted.get_json() == {"message": "Notification deleted"}

    assert (
        client.get(f"/api/notifications/{notification_id}", headers=headers).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/notifications/{notification_id}", headers=headers
        ).status_code
        == 404
    )
