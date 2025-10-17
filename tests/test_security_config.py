"""Boot-time security configuration: JWT fail-fast and the upload cap."""
from __future__ import annotations

import dataclasses

import pytest

from app import create_app
from app.config import DEFAULT_JWT_SECRET, Settings
from tests.support.fake_mongo import FakeMongoClient


def _production_settings(**overrides) -> Settings:
    base = dataclasses.replace(
        Settings.for_testing(), env="production", jwt_secret=DEFAULT_JWT_SECRET
    )
    return dataclasses.replace(base, **overrides)


def test_production_boot_fails_with_builtin_jwt_secret():
    with pytest.raises(RuntimeError, match="JWT secret"):
        create_app(
            settings=_production_settings(), mongo_client=FakeMongoClient()
        )


def test_production_boot_allows_explicit_insecure_opt_out():
    application = create_app(
        settings=_production_settings(allow_insecure_jwt=True),
        mongo_client=FakeMongoClient(),
    )
    rules = {str(rule) for rule in application.url_map.iter_rules()}
    assert "/api/health" in rules


def test_development_boot_still_works_with_builtin_jwt_secret():
    application = create_app(
        settings=Settings.for_testing(), mongo_client=FakeMongoClient()
    )
    assert application.config["JWT_SECRET_KEY"]


def test_payload_over_upload_limit_returns_json_413():
    application = create_app(
        settings=dataclasses.replace(Settings.for_testing(), max_upload_mb=1),
        mongo_client=FakeMongoClient(),
    )
    client = application.test_client()
    oversized = "x" * (1_500_000)
    response = client.post(
        "/api/auth/signup",
        json={"name": oversized, "email": "big@example.com", "password": "pw123456"},
    )
    assert response.status_code == 413
    assert response.get_json() == {"message": "Request payload too large"}
