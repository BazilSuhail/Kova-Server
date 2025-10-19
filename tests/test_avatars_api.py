"""Selectable, server-hosted avatars (feature 15 — customisation)."""
from __future__ import annotations


def test_avatar_catalogue_lists_seeded_avatars(client):
    response = client.get("/api/users/avatars")
    assert response.status_code == 200
    avatars = response.get_json()["avatars"]
    assert avatars, "expected at least one seeded avatar"
    assert "avatar1" in {entry["id"] for entry in avatars}

    first = avatars[0]
    assert first["url"].startswith("/api/users/avatars/")
    assert first["filename"].endswith((".svg", ".png", ".jpg", ".jpeg", ".webp"))


def test_avatar_image_is_served_publicly(client):
    # No Authorization header: avatars are non-sensitive static assets.
    response = client.get("/api/users/avatars/avatar1.svg")
    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
    assert b"<svg" in response.data


def test_unknown_avatar_image_returns_404_json(client):
    response = client.get("/api/users/avatars/does-not-exist.svg")
    assert response.status_code == 404
    assert response.get_json() == {"message": "Avatar not found"}


def test_setting_avatar_id_updates_profile_picture(client, auth):
    response = client.put(
        "/api/users/profile", headers=auth(), json={"avatarId": "avatar2"}
    )
    assert response.status_code == 200
    assert response.get_json()["profilePicture"] == "/api/users/avatars/avatar2.svg"


def test_unknown_avatar_id_is_rejected(client, auth):
    response = client.put(
        "/api/users/profile", headers=auth(), json={"avatarId": "not-a-real-avatar"}
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "Unknown avatar"}


def test_avatar_filename_cannot_escape_the_catalogue(client):
    """A traversal-shaped filename never resolves to a real file."""
    response = client.get("/api/users/avatars/%2e%2e%2f%2e%2e%2fconfig.py")
    assert response.status_code == 404
