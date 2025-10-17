"""Registration, credential checks, token revocation; hashes live here."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import bcrypt
from bson import ObjectId

from ..core.exceptions import AuthenticationError, NotFoundError, ValidationError
from ..repositories.token_blocklist_repository import TokenBlocklistRepository
from ..repositories.user_repository import UserRepository

# Pinned explicitly so a bcrypt library default change can't silently weaken hashes.
PASSWORD_HASH_ROUNDS = 12
MIN_PASSWORD_LENGTH = 8


class AuthService:
    """Owns signup/authentication/token-revocation rules; routes mint JWTs."""

    def __init__(
        self,
        users: UserRepository,
        tokens: TokenBlocklistRepository | None = None,
    ) -> None:
        self._users = users
        self._tokens = tokens

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
                data["password"].encode("utf-8"),
                bcrypt.gensalt(rounds=PASSWORD_HASH_ROUNDS),
            ).decode("utf-8"),
            "profilePicture": data.get("profilePicture", ""),
            "preferences": data.get(
                "preferences", {"theme": "light", "notificationsEnabled": True}
            ),
            "createdAt": datetime.now(UTC).isoformat(),
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

    def get_profile(self, user_id: str) -> dict[str, Any]:
        """Public profile for ``GET /api/auth/me`` (hash projected out)."""
        user = self._users.find_by_user_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> None:
        """Rotate the password after re-proving the current one.

        Raises ``AuthenticationError`` (401) for a wrong current password and
        ``ValidationError`` (400) for a weak new one.
        """
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"New password must be at least {MIN_PASSWORD_LENGTH} characters"
            )
        user = self._users.find_with_password(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if not bcrypt.checkpw(
            current_password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            raise AuthenticationError("Current password is incorrect")
        hashed = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt(rounds=PASSWORD_HASH_ROUNDS),
        ).decode("utf-8")
        self._users.update_fields(user_id, {"password": hashed})

    def revoke(self, jti: str, token_type: str, user_id: str, exp: int) -> None:
        """Blacklist one token until its own expiry (``exp`` is unix seconds)."""
        if self._tokens is None or not jti:
            return
        expires_at = datetime.fromtimestamp(exp, tz=UTC)
        self._tokens.revoke(jti, token_type, user_id, expires_at)

    def is_revoked(self, jti: str) -> bool:
        """Blocklist lookup used by the JWT manager on every protected request."""
        if self._tokens is None or not jti:
            return False
        return self._tokens.is_revoked(jti)
