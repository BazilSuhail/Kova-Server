"""Registration and credential checks; password hashing policy lives here."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import bcrypt
from bson import ObjectId

from ..core.exceptions import AuthenticationError, ValidationError
from ..repositories.user_repository import UserRepository


class AuthService:
    """Owns signup/authentication rules; issues nothing — routes mint JWTs."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def signup(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a user; raises ``ValidationError`` when the email is taken.

        The 400 (not 409) for a duplicate email is the legacy contract and is
        kept intentionally so existing clients do not change.
        """
        email = data["email"]
        if self._users.find_by_email(email) is not None:
            raise ValidationError("Email already exists")
        user = {
            "userId": str(ObjectId()),
            "name": data["name"],
            "email": email,
            "password": bcrypt.hashpw(
                data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8"),
            "profilePicture": data.get("profilePicture", ""),
            "preferences": data.get(
                "preferences", {"theme": "light", "notificationsEnabled": True}
            ),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        return self._users.insert(user)

    def authenticate(self, email: str, password: str) -> dict[str, Any]:
        """Return the user for valid credentials.

        Raises ``AuthenticationError`` with the same two messages the legacy
        service produced (both mapped to 401).
        """
        user = self._users.find_by_email(email)
        if user is None:
            raise AuthenticationError("User not found")
        if not bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            raise AuthenticationError("Invalid password")
        return user
