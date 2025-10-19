"""Auth routes: public signup/login/refresh and JWT-protected session endpoints.

Payload validation happens at the edge; credential, revocation, and password
rules live in ``AuthService``. Tokens are minted here (flask-jwt-extended
concern), never in services. The credential-facing views carry the stricter
per-IP rate limit from ``KOVA_RATELIMIT_AUTH`` (brute-force protection).
"""
from __future__ import annotations

from flask import Blueprint, Response, current_app, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from jwt.exceptions import PyJWTError

from ..core.exceptions import AuthenticationError
from ..core.responses import api_response
from ..core.validation import require_fields
from ..extensions import limiter
from ..services import get_services

auth_bp = Blueprint("auth", __name__)

_REQUIRED_SIGNUP_FIELDS = ("name", "email", "password")
_REQUIRED_LOGIN_FIELDS = ("email", "password")


def _auth_rate() -> str:
    """Auth rate-limit string for this app (settings-driven, read per request)."""
    return current_app.config["KOVA_RATELIMIT_AUTH"]


def _decode(token: str) -> dict:
    """Decode a token from a body; expired/garbage input → 401."""
    try:
        return decode_token(token)
    except PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc


def _issue_tokens(user_id: str) -> dict[str, str]:
    """Mint the access/refresh pair both login and refresh return."""
    return {
        "access_token": create_access_token(identity=user_id),
        "refresh_token": create_refresh_token(identity=user_id),
        "userId": user_id,
    }


@auth_bp.route("/signup", methods=["POST"])
@limiter.limit(_auth_rate)
def signup() -> Response:
    """Create a user and return an access + refresh token (public)."""
    data = require_fields(request.get_json(), *_REQUIRED_SIGNUP_FIELDS)
    user = get_services().auth.signup(dict(data))
    tokens = _issue_tokens(user["userId"])
    return api_response(
        {"message": "User created", **tokens},
        201,
    )


@auth_bp.route("/login", methods=["POST"])
@limiter.limit(_auth_rate)
def login() -> Response:
    """Exchange credentials for an access + refresh token (public)."""
    data = require_fields(request.get_json(), *_REQUIRED_LOGIN_FIELDS)
    user = get_services().auth.authenticate(data["email"], data["password"])
    return api_response(_issue_tokens(user["userId"]), 200)


@auth_bp.route("/refresh", methods=["POST"])
@limiter.limit(_auth_rate)
def refresh() -> Response:
    """Exchange a valid refresh token for a fresh access/refresh pair (public).

    The old refresh token is revoked (rotation), so a stolen token stops
    working the moment the legitimate client refreshes.
    """
    data = require_fields(
        request.get_json(),
        "refresh_token",
        message="refresh_token is required",
        truthy=True,
    )
    claims = _decode(data["refresh_token"])
    if claims.get("type") != "refresh":
        raise AuthenticationError("Not a refresh token")
    auth = get_services().auth
    if auth.is_revoked(claims["jti"]):
        raise AuthenticationError("Token revoked")
    user_id = claims["sub"]
    # The account may have been deleted while the token was still live.
    auth.get_profile(user_id)  # raises 404 → treated as an unusable session
    auth.revoke(claims["jti"], "refresh", user_id, claims["exp"])
    return api_response(_issue_tokens(user_id), 200)


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout() -> Response:
    """Revoke the caller's access token plus an optional refresh token.

    Both requests are idempotent: revoking an already-dead token is a no-op,
    so a client can always log out successfully.
    """
    user_id = get_jwt_identity()
    auth = get_services().auth
    access = get_jwt()
    auth.revoke(access["jti"], "access", user_id, access["exp"])

    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")
    if refresh_token:
        try:
            claims = decode_token(refresh_token)
        except PyJWTError:
            claims = None
        if (
            claims is not None
            and claims.get("type") == "refresh"
            and claims.get("sub") == user_id
        ):
            auth.revoke(claims["jti"], "refresh", user_id, claims["exp"])
    return api_response({"message": "Logged out"}, 200)


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me() -> Response:
    """The authenticated user's profile (public fields only)."""
    return api_response(get_services().auth.get_profile(get_jwt_identity()), 200)


@auth_bp.route("/password", methods=["PUT"])
@jwt_required()
@limiter.limit(_auth_rate)
def change_password() -> Response:
    """Rotate the caller's password after verifying the current one."""
    data = require_fields(
        request.get_json(),
        "currentPassword",
        "newPassword",
        message="currentPassword and newPassword are required",
        truthy=True,
    )
    get_services().auth.change_password(
        get_jwt_identity(), data["currentPassword"], data["newPassword"]
    )
    return api_response({"message": "Password updated"}, 200)
