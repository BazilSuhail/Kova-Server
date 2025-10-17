"""Flask extension initialisation, kept out of the app factory for clarity."""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import Settings


def init_jwt(app: Flask, settings: Settings) -> None:
    """Configure stateless JWT auth with the knobs the legacy config used.

    Also installs the revocation check: every ``jwt_required`` request looks its
    token's ``jti`` up in the blocklist, which is what makes ``logout`` take
    effect immediately instead of after the access token expires.
    """
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret
    # flask-jwt-extended coerces int seconds to a timedelta (legacy passed 3600).
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = settings.jwt_expires_seconds
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = settings.jwt_refresh_expires_seconds
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def _is_token_revoked(_jwt_header: dict, jwt_payload: dict) -> bool:
        # Lazy import: services depend on Flask state, not on this module, but
        # deferring keeps module import order irrelevant.
        from .services import get_services as _get_services

        return _get_services().auth.is_revoked(jwt_payload.get("jti", ""))


def init_cors(app: Flask, settings: Settings) -> None:
    """Apply the configured origin allowlist (``ZENFLOW_CORS_ORIGINS``).

    Default is ``("*",)`` — identical to the legacy ``CORS(app)`` — so no
    deployment breaks until an allowlist is deliberately configured.
    """
    CORS(app, origins=list(settings.cors_origins))
