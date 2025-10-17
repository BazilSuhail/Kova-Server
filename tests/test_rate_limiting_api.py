"""Rate limiting: auth throttling, JSON 429s, and health-probe exemption."""
from __future__ import annotations

import dataclasses

from app import create_app
from app.config import Settings
from flask_jwt_extended import create_access_token

from tests.support.fake_mongo import FakeMongoClient


def _app(**overrides):
    settings = dataclasses.replace(Settings.for_testing(), **overrides)
    application = create_app(settings=settings, mongo_client=FakeMongoClient())
    application.config["TESTING"] = True
    application.config["PROPAGATE_EXCEPTIONS"] = False
    return application


def _token(application) -> str:
    """Mint an access token directly — no signup request to skew counters."""
    with application.app_context():
        return create_access_token(identity="rate-limit-user")


def test_login_trips_auth_rate_limit_and_returns_json_429():
    application = _app(rate_limit_auth="3 per minute")
    client = application.test_client()

    statuses = [
        client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        ).status_code
        for _ in range(4)
    ]
    assert statuses[:3] == [401, 401, 401]  # under the limit: normal auth errors
    assert statuses[3] == 429

    # The body is JSON like the rest of the API, and limiter headers are on.
    breach = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "whatever"},
    )
    assert breach.status_code == 429
    assert breach.get_json() == {"message": "Rate limit exceeded"}
    assert breach.headers.get("X-RateLimit-Limit") is not None
    assert breach.headers.get("Retry-After") is not None


def test_health_probes_are_exempt_from_the_default_limit():
    application = _app(rate_limit_default="1 per minute")
    client = application.test_client()
    # A strict 1/min default must not throttle orchestrator probes.
    for _ in range(3):
        assert client.get("/api/health").status_code == 200
    for _ in range(3):
        assert client.get("/api/health/ready").status_code == 200


def test_default_limit_applies_to_regular_routes():
    application = _app(rate_limit_default="1 per minute")
    client = application.test_client()
    headers = {"Authorization": f"Bearer {_token(application)}"}

    first = client.get("/api/tasks/", headers=headers)
    second = client.get("/api/tasks/", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.get_json() == {"message": "Rate limit exceeded"}


def test_rate_limiting_can_be_disabled_via_settings():
    application = _app(rate_limit_enabled=False, rate_limit_auth="1 per minute")
    client = application.test_client()
    statuses = [
        client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        ).status_code
        for _ in range(3)
    ]
    assert statuses == [401, 401, 401]  # never 429 while disabled
