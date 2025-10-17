"""Flask extension initialisation, kept out of the app factory for clarity."""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .config import Settings


def init_jwt(app: Flask, settings: Settings) -> None:
    """Configure stateless JWT auth with the same knobs the legacy config used."""
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret
    # flask-jwt-extended coerces int seconds to a timedelta (legacy passed 3600).
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = settings.jwt_expires_seconds
    JWTManager(app)


def init_cors(app: Flask, settings: Settings) -> None:
    """Apply the configured origin allowlist (``ZENFLOW_CORS_ORIGINS``).

    Default is ``("*",)`` — identical to the legacy ``CORS(app)`` — so no
    deployment breaks until an allowlist is deliberately configured.
    """
    CORS(app, origins=list(settings.cors_origins))
