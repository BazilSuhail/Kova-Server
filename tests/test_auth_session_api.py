"""Session endpoints: refresh rotation, logout revocation, /me, password change."""
from __future__ import annotations


def _login(client, email="ada@example.com", password="pw123456"):
    return client.post(
        "/api/auth/login", json={"email": email, "password": password}
    ).get_json()


def test_signup_and_login_both_issue_refresh_token(client):
    signup = client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    assert signup.status_code == 201
    assert signup.get_json()["refresh_token"]

    login = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "pw123456"},
    )
    assert login.status_code == 200
    assert login.get_json()["refresh_token"]


def test_refresh_exchanges_refresh_token_for_new_pair(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"]
    assert body["refresh_token"] != tokens["refresh_token"]
    assert body["userId"] == tokens["userId"]


def test_refresh_rotates_so_old_refresh_token_stops_working(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    first = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200
    # The original refresh token was revoked by the rotation above.
    replay = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert replay.status_code == 401


def test_refresh_rejects_access_token_used_as_refresh(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert response.status_code == 401
    assert response.get_json()["message"] == "Not a refresh token"


def test_refresh_rejects_garbage_and_missing_tokens(client):
    missing = client.post("/api/auth/refresh", json={})
    assert missing.status_code == 400
    garbage = client.post(
        "/api/auth/refresh", json={"refresh_token": "not.a.jwt"}
    )
    assert garbage.status_code == 401


def test_logout_revokes_access_and_refresh_tokens(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/api/auth/me", headers=auth).status_code == 200

    logout = client.post(
        "/api/auth/logout",
        headers=auth,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 200
    assert logout.get_json() == {"message": "Logged out"}

    # Access token dead immediately…
    assert client.get("/api/auth/me", headers=auth).status_code == 401
    # …and so is the refresh token.
    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401


def test_logout_succeeds_without_refresh_token_in_body(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = client.post("/api/auth/logout", headers=auth)
    assert response.status_code == 200
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_me_returns_profile_without_password_hash(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["email"] == "ada@example.com"
    assert body["userId"] == tokens["userId"]
    assert "password" not in body


def test_me_returns_401_without_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_change_password_successfully_rotates_credentials(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = client.put(
        "/api/auth/password",
        headers=auth,
        json={"currentPassword": "pw123456", "newPassword": "new-secret-9"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Password updated"}

    old = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "pw123456"},
    )
    assert old.status_code == 401
    new = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "new-secret-9"},
    )
    assert new.status_code == 200


def test_change_password_rejects_wrong_current_password(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    response = client.put(
        "/api/auth/password",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"currentPassword": "wrong-password", "newPassword": "new-secret-9"},
    )
    assert response.status_code == 401
    assert response.get_json()["message"] == "Current password is incorrect"


def test_change_password_rejects_weak_or_missing_new_password(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    tokens = _login(client)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    weak = client.put(
        "/api/auth/password",
        headers=auth,
        json={"currentPassword": "pw123456", "newPassword": "short"},
    )
    assert weak.status_code == 400

    missing = client.put("/api/auth/password", headers=auth, json={})
    assert missing.status_code == 400
