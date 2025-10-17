"""Public auth routes: validate payloads and mint JWTs; rules live in AuthService."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import create_access_token

from ..core.responses import api_response
from ..services import get_services

auth_bp = Blueprint("auth", __name__)

_REQUIRED_SIGNUP_FIELDS = ("name", "email", "password")
_REQUIRED_LOGIN_FIELDS = ("email", "password")


@auth_bp.route("/signup", methods=["POST"])
def signup() -> Response:
    """Create a user and return an access token (public endpoint)."""
    data = request.get_json()
    if not data or not all(key in data for key in _REQUIRED_SIGNUP_FIELDS):
        return api_response({"message": "Missing required fields"}, 400)
    user = get_services().auth.signup(data)
    access_token = create_access_token(identity=user["userId"])
    return api_response(
        {
            "message": "User created",
            "access_token": access_token,
            "userId": user["userId"],
        },
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login() -> Response:
    """Exchange credentials for an access token (public endpoint)."""
    data = request.get_json()
    if not data or not all(key in data for key in _REQUIRED_LOGIN_FIELDS):
        return api_response({"message": "Missing required fields"}, 400)
    user = get_services().auth.authenticate(data["email"], data["password"])
    access_token = create_access_token(identity=user["userId"])
    return api_response(
        {"access_token": access_token, "userId": user["userId"]}, 200
    )
