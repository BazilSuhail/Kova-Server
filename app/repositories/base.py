"""Shared helpers over a single Mongo collection.

Kept deliberately thin: no business rules, no Flask imports — just the query
operators the application actually uses, so services stay storage-agnostic and
the test suite can substitute one fake collection instead of Mongo itself.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, UpdateResult


def utcnow_iso() -> str:
    """Single timestamp source so ``createdAt``/``updatedAt`` stay comparable."""
    return datetime.now(UTC).isoformat()


class BaseRepository:
    """Wraps one collection with insert/find/update/delete primitives."""

    def __init__(self, db: Database, collection_name: str) -> None:
        self._collection: Collection = db[collection_name]

    @property
    def collection(self) -> Collection:
        """Raw collection, for the rare query no helper covers."""
        return self._collection

    def insert(self, document: dict[str, Any]) -> dict[str, Any]:
        """Insert ``document`` and return it unchanged (ids are app-generated).

        ``updatedAt`` is stamped here (falling back to ``createdAt``) so every
        stored row is delta-sync visible without each service remembering to.
        """
        document.setdefault("updatedAt", document.get("createdAt") or utcnow_iso())
        self._collection.insert_one(document)
        return document

    def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
    ) -> dict[str, Any] | None:
        return self._collection.find_one(query, projection)

    def find_many(
        self,
        query: dict[str, Any],
        sort: tuple[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        cursor = self._collection.find(query)
        if sort is not None:
            cursor = cursor.sort(*sort)
        return list(cursor)

    def count(self, query: dict[str, Any]) -> int:
        """Matching-document count (drives pagination metadata)."""
        return self._collection.count_documents(query)

    def find_page(
        self,
        query: dict[str, Any],
        *,
        sort: tuple[str, int] | None = None,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """One page of ``query`` — slicing happens in Mongo, not in Python."""
        cursor = self._collection.find(query)
        if sort is not None:
            cursor = cursor.sort(*sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update(self, query: dict[str, Any], fields: dict[str, Any]) -> UpdateResult:
        """Apply a ``$set``; ``modified_count`` distinguishes "matched" from "changed".

        ``updatedAt`` is stamped **only when something actually changed** so the
        legacy "no-op update looks like a miss" contract is preserved while the
        document still carries a delta-sync timestamp.
        """
        result = self._collection.update_one(query, {"$set": fields})
        if result.modified_count:
            self._collection.update_one(query, {"$set": {"updatedAt": utcnow_iso()}})
        return result

    def find_updated_since(
        self,
        user_id: str,
        since: str | None,
        *,
        sort: tuple[str, int] | None = None,
    ) -> list[dict[str, Any]]:
        """Owner-scoped delta query for offline sync (``updatedAt`` > ``since``)."""
        query: dict[str, Any] = {"userId": user_id}
        if since:
            query["updatedAt"] = {"$gt": since}
        return self.find_many(query, sort=sort)

    def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        return self._collection.delete_one(query)

    def delete_many(self, query: dict[str, Any]) -> DeleteResult:
        return self._collection.delete_many(query)
