"""Profile endpoints: read, update (incl. email collision), delete, auth guard."""
from __future__ import annotations


def test_get_profile_returns_user_without_password(client, auth):
    headers = auth(email="profile@example.com")
    response = client.get("/api/users/profile", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert body["email"] == "profile@example.com"
    assert "password" not in body


def test_get_profile_returns_401_without_token(client):
    assert client.get("/api/users/profile").status_code == 401


def test_update_profile_returns_200_and_new_name(client, auth):
    headers = auth()
    response = client.put(
        "/api/users/profile", headers=headers, json={"name": "New Name"}
    )
    assert response.status_code == 200
    assert response.get_json()["name"] == "New Name"


def test_update_profile_returns_400_when_email_belongs_to_other_user(client, auth):
    auth(email="taken@example.com")
    other_headers = auth(email="other@example.com")
    response = client.put(
        "/api/users/profile", headers=other_headers, json={"email": "taken@example.com"}
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "Email already in use"


def test_delete_profile_returns_200_then_profile_is_gone(client, auth):
    headers = auth(email="delete-me@example.com")
    assert client.delete("/api/users/profile", headers=headers).status_code == 200
    # Token stays valid; the account behind it no longer exists.
    assert client.get("/api/users/profile", headers=headers).status_code == 404


# --- Account deletion cascade (returns counts; removes owned rows) ----------


def _client_with_db():
    """Client wired to a private fake database we can inspect directly."""
    from app import create_app
    from app.config import Settings

    from tests.support.fake_mongo import FakeMongoClient

    mongo = FakeMongoClient()
    application = create_app(settings=Settings.for_testing(), mongo_client=mongo)
    application.config["TESTING"] = True
    application.config["PROPAGATE_EXCEPTIONS"] = False
    return application.test_client(), mongo.get_database()


def _signup(client, email: str = "cascade@example.com") -> dict[str, str]:
    response = client.post(
        "/api/auth/signup",
        json={"name": "Cascade", "email": email, "password": "secret123"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def test_delete_profile_cascades_to_every_owned_collection():
    client, db = _client_with_db()
    headers = _signup(client)

    task = client.post(
        "/api/tasks/", headers=headers, json={"title": "Ship it"}
    ).get_json()
    # Subtasks are owner-less: they hang off the parent task id.
    db["subtasks"].insert_one(
        {"subtaskId": "sub-1", "taskId": task["taskId"], "subTasks": []}
    )
    client.post("/api/planner/", headers=headers, json={"date": "2030-01-01"})
    client.post(
        "/api/notifications/",
        headers=headers,
        json={"title": "Hi", "message": "There"},
    )
    client.post("/api/mood/", headers=headers, json={"mood": "good"})
    client.post("/api/reflections/", headers=headers, json={"text": "Fine."})
    client.post(
        "/api/reminders/",
        headers=headers,
        json={"title": "Stand up", "fireAt": "2030-01-01"},
    )
    client.post(
        "/api/devices/",
        headers=headers,
        json={"expoPushToken": "ExponentPushToken[x]"},
    )

    assert client.delete("/api/users/profile", headers=headers).status_code == 200

    for collection in (
        "users",
        "tasks",
        "subtasks",
        "planner",
        "notifications",
        "mood_entries",
        "reflections",
        "scheduled_reminders",
        "push_devices",
    ):
        assert db[collection].count_documents({}) == 0, collection


def test_delete_profile_leaves_other_users_data_untouched():
    client, db = _client_with_db()
    alice = _signup(client, "alice@example.com")
    bob = _signup(client, "bob@example.com")

    client.post("/api/tasks/", headers=alice, json={"title": "Alice task"})
    client.post("/api/tasks/", headers=bob, json={"title": "Bob task"})

    client.delete("/api/users/profile", headers=alice)

    assert db["tasks"].count_documents({}) == 1
    assert client.get("/api/tasks/", headers=bob).get_json()[0]["title"] == "Bob task"


def test_deleting_an_already_deleted_account_returns_404():
    client, _ = _client_with_db()
    headers = _signup(client, "gone@example.com")
    assert client.delete("/api/users/profile", headers=headers).status_code == 200
    assert client.delete("/api/users/profile", headers=headers).status_code == 404
