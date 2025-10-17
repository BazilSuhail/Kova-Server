"""Flask extension initialisation, kept out of the app factory for clarity."""
from __future__ import annotations

from flask import Flask, current_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import Settings

# Singleton limiter: view/blueprint decorators bind to it at import time, and
# ``init_app`` gives *each* app its own fresh storage (per-process memory by
# default) — which is also what keeps test apps isolated from each other.
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


def _default_rate_limit() -> str:
    """App-wide default limit for the *current* app (flask-limiter call-time hook)."""
    return current_app.config["ZENFLOW_RATELIMIT_DEFAULT"]


def init_limiter(app: Flask, settings: Settings) -> None:
    """Configure rate limiting (flask-limiter).

    Every route gets ``ZENFLOW_RATELIMIT_DEFAULT`` (600/min per IP); the auth
    views override it with the stricter ``ZENFLOW_RATELIMIT_AUTH``. Health
    probes are exempt — orchestrators must never be throttled.
    """
    app.config["RATELIMIT_ENABLED"] = settings.rate_limit_enabled
    # flask-limiter snapshots RATELIMIT_DEFAULT when the *first* app in the
    # process inits (plain strings are baked into the shared limit manager), so
    # a later app's value would be ignored. A callable provider is re-resolved
    # on every request instead — one shared limiter, per-app values.
    app.config["ZENFLOW_RATELIMIT_DEFAULT"] = settings.rate_limit_default
    app.config["RATELIMIT_DEFAULT"] = _default_rate_limit
    app.config["RATELIMIT_STORAGE_URI"] = settings.rate_limit_storage_uri
    app.config["RATELIMIT_HEADERS_ENABLED"] = True
    # Read by the auth views through a callable limit (evaluated per request).
    app.config["ZENFLOW_RATELIMIT_AUTH"] = settings.rate_limit_auth
    limiter.init_app(app)

    from .api.health import health_bp  # late import: avoids an api↔extensions cycle

    limiter.exempt(health_bp)


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
