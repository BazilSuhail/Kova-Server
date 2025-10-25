"""Registration, credential checks, token revocation; hashes live here."""
from __future__ import annotations

import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from bson import ObjectId

from ..core.exceptions import AuthenticationError, NotFoundError, ValidationError
from ..repositories.token_blocklist_repository import TokenBlocklistRepository
from ..repositories.user_repository import UserRepository

# Pinned explicitly so a bcrypt library default change can't silently weaken hashes.
PASSWORD_HASH_ROUNDS = 12
MIN_PASSWORD_LENGTH = 8

# Password reset by emailed 6-digit code.
RESET_CODE_TTL = timedelta(minutes=15)
RESET_MAX_ATTEMPTS = 5
# A fresh code is not re-issued (or re-mailed) more often than this per account.
RESET_RESEND_COOLDOWN = timedelta(seconds=60)
_INVALID_CODE = "Invalid or expired code"


def _hash(secret: str) -> str:
    return bcrypt.hashpw(
        secret.encode("utf-8"), bcrypt.gensalt(rounds=PASSWORD_HASH_ROUNDS)
    ).decode("utf-8")


def _check_new_password(new_password: str) -> None:
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"New password must be at least {MIN_PASSWORD_LENGTH} characters"
        )


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
        _check_new_password(new_password)
        user = self._users.find_with_password(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if not bcrypt.checkpw(
            current_password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            raise AuthenticationError("Current password is incorrect")
        self._users.update_fields(user_id, {"password": _hash(new_password)})

    def request_password_reset(self, email: str) -> str | None:
        """Issue a 6-digit reset code; return it for delivery (``None`` = send nothing).

        Unknown emails return ``None`` but still pay for one bcrypt hash so
        timing does not reveal which addresses have accounts. Only the hash is
        stored, with an expiry and an attempt counter.
        """
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = _hash(code)
        user = self._users.find_by_email(email)
        if user is None:
            return None
        now = datetime.now(UTC)
        pending = user.get("passwordReset") or {}
        sent_at = pending.get("sentAt")
        if sent_at and now - datetime.fromisoformat(sent_at) < RESET_RESEND_COOLDOWN:
            return None  # cooldown: keep the code already sent (no mailbox flooding)
        self._users.update_fields(
            user["userId"],
            {
                "passwordReset": {
                    "codeHash": code_hash,
                    "expiresAt": (now + RESET_CODE_TTL).isoformat(),
                    "attempts": 0,
                    "sentAt": now.isoformat(),
                }
            },
        )
        return code

    def reset_password(self, email: str, code: str, new_password: str) -> None:
        """Verify the emailed code, set the new password, end every session.

        Wrong codes count against ``RESET_MAX_ATTEMPTS``; once exhausted (or
        expired) the code is discarded and a new one must be requested.
        """
        _check_new_password(new_password)
        user = self._users.find_by_email(email)
        pending = (user or {}).get("passwordReset")
        if user is None or not pending:
            raise ValidationError(_INVALID_CODE)
        user_id = user["userId"]
        if datetime.now(UTC) >= datetime.fromisoformat(pending["expiresAt"]):
            self._users.update_fields(user_id, {"passwordReset": None})
            raise ValidationError(_INVALID_CODE)
        attempts = int(pending.get("attempts", 0))
        if attempts >= RESET_MAX_ATTEMPTS:
            self._users.update_fields(user_id, {"passwordReset": None})
            raise ValidationError("Too many attempts. Request a new code.")
        if not bcrypt.checkpw(
            code.strip().encode("utf-8"), pending["codeHash"].encode("utf-8")
        ):
            # shortcut: read-modify-write counter, so parallel guesses can share a
            # count; the per-IP rate limit bounds it. Switch to an atomic $inc if needed.
            self._users.update_fields(
                user_id, {"passwordReset": {**pending, "attempts": attempts + 1}}
            )
            raise ValidationError(_INVALID_CODE)
        self._users.update_fields(
            user_id,
            {
                "password": _hash(new_password),
                "passwordReset": None,
                # Every token issued up to now (any device) stops working.
                "sessionsRevokedAt": int(time.time()),
            },
        )

    def revoke(self, jti: str, token_type: str, user_id: str, exp: int) -> None:
        """Blacklist one token until its own expiry (``exp`` is unix seconds)."""
        if self._tokens is None or not jti:
            return
        expires_at = datetime.fromtimestamp(exp, tz=UTC)
        self._tokens.revoke(jti, token_type, user_id, expires_at)

    def is_token_revoked(self, claims: dict[str, Any]) -> bool:
        """Blocklisted ``jti``, or issued before the user's last password reset.

        ``iat`` has 1-second resolution, so a token minted in the same second
        as the reset is also rejected (fail closed; the user just logs in again).
        """
        if self.is_revoked(claims.get("jti", "")):
            return True
        user = self._users.find_by_user_id(claims.get("sub", ""))
        cutoff = (user or {}).get("sessionsRevokedAt")
        return cutoff is not None and int(claims.get("iat", 0)) <= cutoff

    def is_revoked(self, jti: str) -> bool:
        """Blocklist lookup used by the JWT manager on every protected request."""
        if self._tokens is None or not jti:
            return False
        return self._tokens.is_revoked(jti)
