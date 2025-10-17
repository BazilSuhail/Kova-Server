"""Structured JSON logging with a per-request correlation id.

Why: the legacy code used ``print()`` — unordered, unparseable, and it leaked
passwords/hashed payloads to stdout.  A single JSON stream on stdout is what
log aggregators (Railway, CloudWatch, Datadog) ingest, and the correlation id
ties every line of one request together.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from flask import g, has_request_context

# Attributes present on every LogRecord; anything else is caller-supplied context.
_RESERVED_RECORD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__) | frozenset(
    {"message", "asctime"}
)

_configured = False


class JsonFormatter(logging.Formatter):
    """Render one log record as a single JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            payload["correlation_id"] = correlation_id
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_ATTRS or key == "correlation_id" or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class CorrelationIdFilter(logging.Filter):
    """Attach the active request's correlation id to every record it sees."""

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context():
            record.correlation_id = getattr(g, "correlation_id", None)
        return True


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON handler on the root logger exactly once per process.

    Idempotent because tests and the app factory may both call it; repeated
    calls only adjust the level so ``-o log_level=DEBUG`` style overrides work.
    """
    global _configured
    root = logging.getLogger()
    if _configured:
        root.setLevel(level.upper())
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(CorrelationIdFilter())

    root.handlers.clear()  # drop Flask/Werkzeug defaults so output stays uniform
    root.addHandler(handler)
    root.setLevel(level.upper())

    # ``--flask-debug`` mode: werkzeug lazily installs its own non-JSON handler
    # unless one already exists, so give it ours and stop double-printing.
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.addHandler(handler)
    werkzeug_logger.propagate = False

    _configured = True
