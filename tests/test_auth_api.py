"""Auth endpoints: signup/login happy paths, validation, and credential errors."""
from __future__ import annotations


def test_signup_returns_token_and_user_when_payload_is_valid(client):
    response = client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["message"] == "User created"
    assert body["access_token"]
    assert body["userId"]


def test_signup_returns_400_when_required_fields_missing(client):
    response = client.post("/api/auth/signup", json={"name": "Ada"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "Missing required fields"}


def test_signup_returns_400_when_email_already_exists(client):
    payload = {"name": "Ada", "email": "dup@example.com", "password": "pw123456"}
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.get_json()["message"] == "Email already exists"


def test_login_returns_token_when_credentials_are_valid(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "pw123456"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"]
    assert body["userId"]


def test_login_returns_401_when_password_is_wrong(client):
    client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid password"


def test_login_returns_401_when_user_does_not_exist(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "pw123456"},
    )
    assert response.status_code == 401
    assert response.get_json()["message"] == "User not found"
