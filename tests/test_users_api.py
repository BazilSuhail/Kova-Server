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
