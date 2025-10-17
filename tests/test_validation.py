"""Unit tests for the shared request-body validation helper."""
from __future__ import annotations

import pytest
from app.core.exceptions import ValidationError
from app.core.validation import require_fields


def test_require_fields_returns_data_when_every_field_is_present():
    data = {"title": "Write", "taskId": "abc"}
    assert require_fields(data, "title", "taskId") is data


def test_require_fields_accepts_missing_optional_fields():
    assert require_fields({"title": "Write"}, "title") == {"title": "Write"}


def test_require_fields_rejects_missing_key_with_exact_message():
    with pytest.raises(ValidationError) as excinfo:
        require_fields({"name": "Ada"}, "email", "password")
    assert excinfo.value.message == "Missing required fields"
    assert excinfo.value.status_code == 400


def test_require_fields_rejects_none_body():
    with pytest.raises(ValidationError):
        require_fields(None, "title", message="Title required")


def test_require_fields_truthy_mode_rejects_empty_values():
    with pytest.raises(ValidationError) as excinfo:
        require_fields(
            {"title": ""}, "title", message="Title and message are required", truthy=True
        )
    assert excinfo.value.message == "Title and message are required"


def test_require_fields_presence_mode_allows_empty_string():
    assert require_fields({"title": ""}, "title") == {"title": ""}
