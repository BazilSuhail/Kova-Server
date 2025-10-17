"""Data access for the ``users`` collection."""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "users")

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        return self.find_one({"email": email})

    def find_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        """Fetch a profile with the password hash projected out at the source."""
        return self.find_one({"userId": user_id}, {"password": 0})

    def find_with_password(self, user_id: str) -> dict[str, Any] | None:
        """Full document — only for credential checks (password change)."""
        return self.find_one({"userId": user_id})

    def email_used_by_other_user(self, email: str, user_id: str) -> bool:
        """Used to reject a profile update that would collide with another account."""
        return self.find_one({"email": email, "userId": {"$ne": user_id}}) is not None

    def update_fields(self, user_id: str, fields: dict[str, Any]) -> int:
        return self.update({"userId": user_id}, fields).modified_count

    def delete_by_user_id(self, user_id: str) -> int:
        return self.delete_one({"userId": user_id}).deleted_count
