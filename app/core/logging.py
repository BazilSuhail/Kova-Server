"""Console logging: a clean emoji UI by default, structured JSON on demand.

The default ``text`` format is what you see running ``python run.py`` — one
readable line per event with an emoji per level. Deployments that ship logs to
an aggregator (Railway, CloudWatch, Datadog, …) can switch to the JSON stream
with ``KOVA_LOG_FORMAT=json``; both formats carry the same per-request
correlation id.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from flask import g, has_request_context


def _utf8(stream: Any) -> Any:
    """Best-effort UTF-8 switch so emoji render on legacy Windows consoles.

    ``run.py`` does this for its own process, but entrypoints like gunicorn or
    a bare ``create_app()`` may not — without it a cp1252 stdout turns every
    log line into a UnicodeEncodeError.
    """
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # detached/closed stream — leave as-is
            pass
    return stream

# Attributes present on every LogRecord; anything else is caller-supplied context.
_RESERVED_RECORD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__) | frozenset(
    {"message", "asctime"}
)

# `correlation_id` is injected by CorrelationIdFilter and rendered explicitly.
_HIDDEN_EXTRA_KEYS = frozenset({"correlation_id"})

# One face per severity — the whole point of the console UI.
_LEVEL_ICONS = {
    "DEBUG": "🔍",
    "INFO": "✅",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "💥",
}

_configured = False


def _extras(record: logging.LogRecord) -> dict[str, Any]:
    """Caller-supplied context attached to a record (``extra={...}``)."""
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in _RESERVED_RECORD_ATTRS
        and key not in _HIDDEN_EXTRA_KEYS
        and not key.startswith("_")
    }


class TextFormatter(logging.Formatter):
    """Clean, human-readable single-line output with an emoji per level.

    Example::

        ✅ 01:45:20  MongoDB connected
        ✅ 01:45:20  Application ready   [env=development, blueprints=19]
        ⚠️ 01:45:20  Using the built-in JWT secret
        ❌ 01:45:21  unhandled_exception   [error_type=RuntimeError]
    """

    def format(self, record: logging.LogRecord) -> str:
        icon = _LEVEL_ICONS.get(record.levelname, "•")
        clock = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        line = f"{icon} {clock}  {record.getMessage()}"
        extras = _extras(record)
        if extras:
            rendered = ", ".join(f"{key}={value}" for key, value in extras.items())
            line += f"   [{rendered}]"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


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
        for key, value in _extras(record).items():
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_FORMATTERS = {"text": TextFormatter, "json": JsonFormatter}


class CorrelationIdFilter(logging.Filter):
    """Attach the active request's correlation id to every record it sees."""

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context():
            record.correlation_id = getattr(g, "correlation_id", None)
        return True


def configure_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Install the console handler on the root logger exactly once per process.

    Idempotent because tests and the app factory may both call it; repeated
    calls only adjust the level so ``KOVA_LOG_LEVEL`` overrides keep working.
    ``fmt`` selects the renderer: ``"text"`` (default, emoji UI) or ``"json"``.
    """
    global _configured
    root = logging.getLogger()
    if _configured:
        root.setLevel(level.upper())
        return

    handler = logging.StreamHandler(_utf8(sys.stdout))
    handler.setFormatter(_FORMATTERS.get(fmt.lower(), TextFormatter)())
    handler.addFilter(CorrelationIdFilter())

    root.handlers.clear()  # drop Flask/Werkzeug defaults so output stays uniform
    root.addHandler(handler)
    root.setLevel(level.upper())

    # ``--flask-debug`` mode: werkzeug lazily installs its own handler unless
    # one already exists, so give it ours and stop double-printing.
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.addHandler(handler)
    werkzeug_logger.propagate = False

    # Third-party libraries are chatty at INFO (APScheduler's scheduling lines,
    # Waitress' bind banner, PyMongo/urllib3 retry chatter). They add nothing to
    # the app's own stream, so hold them at WARNING and above.
    for noisy in ("apscheduler", "waitress", "pymongo", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True
