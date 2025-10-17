"""Shared fixtures: one fully wired app per test against an in-memory database."""
from __future__ import annotations

import pytest
from app import create_app
from app.config import Settings

from tests.support.fake_mongo import FakeMongoClient


@pytest.fixture()
def app():
    """A fresh app + empty fake database for every test (perfect isolation)."""
    application = create_app(
        settings=Settings.for_testing(), mongo_client=FakeMongoClient()
    )
    application.config["TESTING"] = True
    # Keep error handlers in charge so 4xx/5xx JSON bodies are assertable
    # instead of exceptions escaping the test client.
    application.config["PROPAGATE_EXCEPTIONS"] = False
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth(client):
    """Factory returning auth headers for a freshly signed-up user."""

    def _auth(
        email: str = "user@example.com", password: str = "secret123"
    ) -> dict[str, str]:
        response = client.post(
            "/api/auth/signup",
            json={"name": "Test User", "email": email, "password": password},
        )
        assert response.status_code == 201
        token = response.get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _auth
