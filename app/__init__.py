"""Application factory: wires configuration, infrastructure, and HTTP together.

``create_app`` is the single composition root — config → extensions → error
handling → database → services → blueprints — so tests can inject settings and
a fake Mongo client without any monkey-patching.
"""
from __future__ import annotations

import logging
import time
import typing as t
import uuid

from flask import Flask, Response, g, request
from werkzeug.exceptions import HTTPException

from .api import register_blueprints
from .config import Settings
from .core.exceptions import AppError
from .core.logging import configure_logging
from .core.responses import api_response
from .core.telemetry import capture_exception, init_sentry
from .db import connect_mongo, init_db
from .extensions import init_cors, init_jwt, init_limiter
from .services import EXTENSION_KEY, build_services

if t.TYPE_CHECKING:
    from pymongo import MongoClient

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    mongo_client: MongoClient | None = None,
) -> Flask:
    """Build and wire the Flask application.

    Args:
        settings: injected by tests; production callers rely on ``Settings.from_env``.
        mongo_client: an already-connected client (tests pass a fake). When
            omitted the app opens its own connection and fails fast if Mongo is
            unreachable — the same startup contract as the legacy factory.

    Returns:
        A fully configured app with all 41 endpoints registered.
    """
    if settings is None:
        settings = Settings.from_env()
    configure_logging(settings.log_level)
    init_sentry(settings)
    _reject_insecure_config(settings)

    app = Flask(__name__)

    # Keys read via ``current_app.config`` by the integration utilities.
    app.config["MONGO_URI"] = settings.mongo_uri
    app.config["FLASK_ENV"] = settings.env
    app.config["GROQ_API_KEY"] = settings.groq_api_key
    app.config["GROQ_LLM_URL"] = settings.groq_llm_url
    app.config["ASSEMBLYAI_API_KEY"] = settings.assemblyai_api_key
    # Reject oversized uploads (voice/PDF) before they are buffered into memory.
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_mb * 1024 * 1024

    init_jwt(app, settings)
    init_cors(app, settings)
    init_limiter(app, settings)
    _register_request_context(app)
    _register_security_headers(app)
    _register_error_handlers(app)

    client = mongo_client if mongo_client is not None else connect_mongo(settings.mongo_uri)
    db = init_db(app, client)
    app.extensions[EXTENSION_KEY] = build_services(db)

    register_blueprints(app)
    logger.info(
        "application_ready",
        extra={"env": settings.env, "blueprints": len(app.blueprints)},
    )
    return app


def _reject_insecure_config(settings: Settings) -> None:
    """Refuse to boot in production with the built-in JWT secret.

    A warning buried in a log stream is easy to miss; a crash at boot is not.
    ``ZENFLOW_ALLOW_INSECURE_JWT=1`` bypasses the check (development only).
    """
    if not settings.uses_default_jwt_secret:
        return
    if settings.env == "production" and not settings.allow_insecure_jwt:
        raise RuntimeError(
            "Refusing to start in production with the built-in JWT secret. "
            "Set ZENFLOW_JWT_SECRET to a random string of at least 32 characters "
            "(or ZENFLOW_ALLOW_INSECURE_JWT=1 to bypass — development only)."
        )
    logger.warning(
        "jwt_secret_insecure_default",
        extra={"env": settings.env, "hint": "set ZENFLOW_JWT_SECRET"},
    )


def _register_security_headers(app: Flask) -> None:
    """Minimal hardening headers on every response.

    JSON API only — no CSP (no HTML to protect) and no HSTS/HTTPS redirect
    (would break local development; handled at the proxy in production).
    """

    @app.after_request
    def _add_security_headers(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


def _register_request_context(app: Flask) -> None:
    """Give every request a correlation id and emit one structured access log."""

    @app.before_request
    def _start_request() -> None:
        # Accept an upstream id so traces stitch across services.
        g.correlation_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        g.started_at = time.perf_counter()

    @app.after_request
    def _finish_request(response: Response) -> Response:
        started_at = getattr(g, "started_at", None)
        duration_ms = (
            round((time.perf_counter() - started_at) * 1000, 2)
            if started_at is not None
            else None
        )
        response.headers["X-Request-ID"] = getattr(g, "correlation_id", "")
        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


def _register_error_handlers(app: Flask) -> None:
    """Translate exceptions into JSON exactly once — routes carry no try/except."""

    @app.errorhandler(AppError)
    def _handle_app_error(error: AppError) -> Response:
        level = logging.ERROR if error.status_code >= 500 else logging.INFO
        logger.log(
            level,
            "request_rejected",
            extra={"status": error.status_code, "error": error.message},
        )
        return api_response(error.to_payload(), error.status_code)

    @app.errorhandler(Exception)
    def _handle_unexpected(error: Exception) -> Response:
        if isinstance(error, HTTPException):
            if error.code == 413:
                # Oversized upload (MAX_CONTENT_LENGTH) → JSON, like the rest
                # of the API, instead of Flask's default HTML error page.
                return api_response({"message": "Request payload too large"}, 413)
            if error.code == 429:
                # Rate limit breach (flask-limiter) → JSON; X-RateLimit-* and
                # Retry-After headers are added by the limiter itself.
                return api_response({"message": "Rate limit exceeded"}, 429)
            # Unmatched URLs/methods keep Flask's default (HTML) responses so
            # the public 404/405 contract does not change.
            return t.cast(Response, error.get_response())
        logger.exception("unhandled_exception", extra={"error_type": type(error).__name__})
        capture_exception(error)
        # Deliberately generic: the legacy ``Server error: {str(e)}`` bodies
        # leaked internals to clients.
        return api_response({"message": "Internal server error"}, 500)
