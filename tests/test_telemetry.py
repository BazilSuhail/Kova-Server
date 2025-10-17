"""Sentry wiring: exceptions are reported only when a DSN is configured."""
from __future__ import annotations

import app.core.telemetry as telemetry
from app.config import Settings
from app.services.task_service import TaskService


class _StubSentry:
    def __init__(self) -> None:
        self.captured: list[BaseException] = []

    def capture_exception(self, error: BaseException) -> None:
        self.captured.append(error)

    def init(self, **_kwargs) -> None:  # pragma: no cover - only used by init_sentry
        raise AssertionError("init must not be reached in these tests")


def test_unexpected_error_is_reported_to_sentry(monkeypatch, client, auth):
    stub = _StubSentry()
    monkeypatch.setattr(telemetry, "sentry_sdk", stub)
    monkeypatch.setattr(telemetry, "_active", True)

    def _boom(self, *_args, **_kwargs):
        raise RuntimeError("database on fire")

    monkeypatch.setattr(TaskService, "list", _boom)

    response = client.get("/api/tasks/", headers=auth())
    assert response.status_code == 500
    assert response.get_json() == {"message": "Internal server error"}
    assert len(stub.captured) == 1
    assert isinstance(stub.captured[0], RuntimeError)


def test_sentry_stays_inert_without_a_dsn(monkeypatch):
    stub = _StubSentry()
    monkeypatch.setattr(telemetry, "sentry_sdk", stub)

    # No ZENFLOW_SENTRY_DSN → init does not arm the SDK…
    telemetry.init_sentry(Settings.for_testing())
    assert telemetry._active is False
    # …and reporting calls are swallowed.
    telemetry.capture_exception(RuntimeError("ignored"))
    assert stub.captured == []
