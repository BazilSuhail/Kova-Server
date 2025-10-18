"""Push-device registration (feature 10)."""
from __future__ import annotations


def test_register_device_returns_201(client, auth):
    response = client.post(
        "/api/devices/",
        headers=auth(),
        json={"expoPushToken": "ExponentPushToken[abc]", "platform": "ios"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["expoPushToken"] == "ExponentPushToken[abc]"
    assert body["platform"] == "ios"
    assert body["deviceId"]


def test_register_device_requires_token(client, auth):
    response = client.post("/api/devices/", headers=auth(), json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "expoPushToken is required"}


def test_register_device_rejects_unknown_platform(client, auth):
    response = client.post(
        "/api/devices/",
        headers=auth(),
        json={"expoPushToken": "ExponentPushToken[x]", "platform": "blackberry"},
    )
    assert response.status_code == 400


def test_token_is_reowned_not_duplicated(client, auth):
    alice = auth("alice@example.com")
    bob = auth("bob@example.com")
    token = {"expoPushToken": "ExponentPushToken[shared]", "platform": "android"}

    client.post("/api/devices/", headers=alice, json=token)
    client.post("/api/devices/", headers=bob, json=token)

    assert client.get("/api/devices/", headers=alice).get_json() == []
    bob_devices = client.get("/api/devices/", headers=bob).get_json()
    assert len(bob_devices) == 1


def test_unregister_device(client, auth):
    headers = auth()
    created = client.post(
        "/api/devices/",
        headers=headers,
        json={"expoPushToken": "ExponentPushToken[gone]"},
    ).get_json()

    deleted = client.delete(f"/api/devices/{created['deviceId']}", headers=headers)
    assert deleted.get_json() == {"message": "Device unregistered"}
    assert (
        client.delete(f"/api/devices/{created['deviceId']}", headers=headers).status_code
        == 404
    )
