"""User profile reads/updates/deletes (the account itself, not its content)."""
from __future__ import annotations

from typing import Any

from ..core.exceptions import NotFoundError, ValidationError
from ..repositories.user_repository import UserRepository

# Fields a client may change through the API — anything else is dropped.
_UPDATABLE_FIELDS = ("name", "email", "profilePicture", "preferences")


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def get_profile(self, user_id: str) -> dict[str, Any]:
        user = self._users.find_by_user_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def update_profile(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Apply whitelisted changes and return the refreshed profile.

        ``modified_count == 0`` covers both "no such user" and "nothing
        actually changed" — the legacy service merged both into one 400 and
        that ambiguity is preserved deliberately.
        """
        fields = {k: v for k, v in data.items() if k in _UPDATABLE_FIELDS}
        if "email" in fields and self._users.email_used_by_other_user(
            fields["email"], user_id
        ):
            raise ValidationError("Email already in use")
        if self._users.update_fields(user_id, fields) == 0:
            raise ValidationError("User not found or no changes made")
        return self.get_profile(user_id)

    def delete_profile(self, user_id: str) -> None:
        """Delete the account document.

        Related tasks/planner/summaries are intentionally left alone: cascade
        deletion was never part of the contract (see docs/TODO.md).
        """
        if self._users.delete_by_user_id(user_id) == 0:
            raise NotFoundError("User not found")
