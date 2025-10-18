"""Data access for the ``tombstones`` collection (feature 14 — offline sync).

A tombstone records that an owner-scoped document was deleted, so an offline
client can prune the row on its next pull instead of resurrecting it.
"""
from __future__ import annotations

from typing import Any

from pymongo.database import Database

from .base import BaseRepository


class TombstoneRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db, "tombstones")

    def record(self, user_id: str, collection: str, doc_id: str, deleted_at: str) -> None:
        self.insert(
            {
                "userId": user_id,
                "collection": collection,
                "docId": doc_id,
                "deletedAt": deleted_at,
                "updatedAt": deleted_at,
            }
        )

    def find_since(self, user_id: str, since: str | None) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"userId": user_id}
        if since:
            query["deletedAt"] = {"$gt": since}
        return self.find_many(query, sort=("deletedAt", 1))
