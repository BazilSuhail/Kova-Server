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
from .db import connect_mongo, init_db
from .extensions import init_cors, init_jwt
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
        A fully configured app with all 29 endpoints registered.
    """
    if settings is None:
        settings = Settings.from_env()
    configure_logging(settings.log_level)

    app = Flask(__name__)

    # Keys read via ``current_app.config`` by the integration utilities.
    app.config["MONGO_URI"] = settings.mongo_uri
    app.config["FLASK_ENV"] = settings.env
    app.config["GROQ_API_KEY"] = settings.groq_api_key
    app.config["GROQ_LLM_URL"] = settings.groq_llm_url
    app.config["ASSEMBLYAI_API_KEY"] = settings.assemblyai_api_key

    init_jwt(app, settings)
    init_cors(app)
    _register_request_context(app)
    _register_error_handlers(app)

    if settings.env == "production" and settings.uses_default_jwt_secret:
        logger.warning(
            "jwt_secret_insecure_default",
            extra={"hint": "set ZENFLOW_JWT_SECRET in the environment"},
        )

    client = mongo_client if mongo_client is not None else connect_mongo(settings.mongo_uri)
    db = init_db(app, client)
    app.extensions[EXTENSION_KEY] = build_services(db)

    register_blueprints(app)
    logger.info(
        "application_ready",
        extra={"env": settings.env, "blueprints": len(app.blueprints)},
    )
    return app


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
            # Unmatched URLs/methods keep Flask's default (HTML) responses so
            # the public 404/405 contract does not change.
            return error.get_response()
        logger.exception("unhandled_exception", extra={"error_type": type(error).__name__})
        # Deliberately generic: the legacy ``Server error: {str(e)}`` bodies
        # leaked internals to clients.
        return api_response({"message": "Internal server error"}, 500)
