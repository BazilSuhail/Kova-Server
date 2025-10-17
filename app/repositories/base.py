"""Shared helpers over a single Mongo collection.

Kept deliberately thin: no business rules, no Flask imports — just the query
operators the application actually uses, so services stay storage-agnostic and
the test suite can substitute one fake collection instead of Mongo itself.
"""
from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult, UpdateResult


class BaseRepository:
    """Wraps one collection with insert/find/update/delete primitives."""

    def __init__(self, db: Database, collection_name: str) -> None:
        self._collection: Collection = db[collection_name]

    @property
    def collection(self) -> Collection:
        """Raw collection, for the rare query no helper covers."""
        return self._collection

    def insert(self, document: dict[str, Any]) -> dict[str, Any]:
        """Insert ``document`` and return it unchanged (ids are app-generated)."""
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

    def update(self, query: dict[str, Any], fields: dict[str, Any]) -> UpdateResult:
        """Apply a ``$set``; ``modified_count`` distinguishes "matched" from "changed"."""
        return self._collection.update_one(query, {"$set": fields})

    def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        return self._collection.delete_one(query)

    def delete_many(self, query: dict[str, Any]) -> DeleteResult:
        return self._collection.delete_many(query)
