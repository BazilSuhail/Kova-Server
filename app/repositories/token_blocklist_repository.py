"""Data access for the token blocklist (logout/refresh-token revocation).

One row per revoked token: ``jti`` is unique, ``expiresAt`` carries a TTL index
so Mongo purges rows on its own once the token could no longer be used anyway.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class TokenBlocklistRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "token_blocklist")

    def revoke(
        self, jti: str, token_type: str, user_id: str, expires_at: datetime
    ) -> dict[str, Any]:
        """Record a revoked token; duplicate ``jti`` (double logout) is a no-op."""
        if self.find_one({"jti": jti}) is not None:
            return {"jti": jti}
        return self.insert(
            {
                "jti": jti,
                "type": token_type,
                "userId": user_id,
                "expiresAt": expires_at,
                "blacklistedAt": datetime.now(UTC).isoformat(),
            }
        )

    def is_revoked(self, jti: str) -> bool:
        return bool(jti) and self.find_one({"jti": jti}) is not None
