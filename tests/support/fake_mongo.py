"""A tiny in-memory stand-in for PyMongo covering exactly the operators used.

Hand-rolled instead of depending on ``mongomock`` so the suite runs offline
with zero extra packages.  Semantics that matter are mirrored faithfully —
notably ``modified_count`` only counting *actual* changes, which is what makes
the API return 404 for a no-op update.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class InsertOneResult:
    inserted_id: Any


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int


@dataclass
class DeleteResult:
    deleted_count: int


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict) and any(str(k).startswith("$") for k in expected):
            for operator, operand in expected.items():
                if operator == "$in":
                    if actual not in operand:
                        return False
                elif operator == "$ne":
                    if actual == operand:
                        return False
                elif operator == "$regex":
                    if not isinstance(actual, str) or not re.search(operand, actual):
                        return False
                else:
                    raise NotImplementedError(f"fake mongo: unsupported operator {operator}")
        elif actual != expected:
            return False
    return True


def _project(document: dict[str, Any], projection: dict[str, int] | None) -> dict[str, Any]:
    if not projection:
        return document
    excluded = {key for key, value in projection.items() if value == 0}
    included = {key for key, value in projection.items() if value == 1}
    if included:
        return {k: v for k, v in document.items() if k in included}
    return {k: v for k, v in document.items() if k not in excluded}


class FakeCursor:
    """Lazy-ish cursor supporting the single ``.sort()`` the app uses."""

    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    def sort(self, key: str, direction: int = 1) -> "FakeCursor":
        self._documents.sort(
            key=lambda doc: doc.get(key) or "", reverse=direction == -1
        )
        return self

    def __iter__(self):
        return iter(self._documents)


class FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self._documents: list[dict[str, Any]] = []

    def create_index(self, *args: Any, **kwargs: Any) -> str:
        """Indexes are irrelevant in memory; accept and ignore."""
        return f"{self.name}_index"

    def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        self._documents.append(copy.deepcopy(document))
        return InsertOneResult(inserted_id=document.get("_id"))

    def find_one(
        self, query: dict[str, Any], projection: dict[str, int] | None = None
    ) -> dict[str, Any] | None:
        for document in self._documents:
            if _matches(document, query):
                return _project(copy.deepcopy(document), projection)
        return None

    def find(self, query: dict[str, Any] | None = None) -> FakeCursor:
        query = query or {}
        return FakeCursor(
            [
                copy.deepcopy(document)
                for document in self._documents
                if _matches(document, query)
            ]
        )

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> UpdateResult:
        if set(update) != {"$set"}:
            raise NotImplementedError(f"fake mongo: unsupported update {set(update)}")
        for index, document in enumerate(self._documents):
            if _matches(document, query):
                candidate = copy.deepcopy(document)
                candidate.update(copy.deepcopy(update["$set"]))
                changed = candidate != document
                self._documents[index] = candidate
                return UpdateResult(matched_count=1, modified_count=1 if changed else 0)
        return UpdateResult(matched_count=0, modified_count=0)

    def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        for index, document in enumerate(self._documents):
            if _matches(document, query):
                del self._documents[index]
                return DeleteResult(deleted_count=1)
        return DeleteResult(deleted_count=0)

    def delete_many(self, query: dict[str, Any]) -> DeleteResult:
        remaining = [d for d in self._documents if not _matches(d, query)]
        deleted = len(self._documents) - len(remaining)
        self._documents = remaining
        return DeleteResult(deleted_count=deleted)


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection(name))

    def __getattr__(self, name: str) -> FakeCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        return self[name]

    def command(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Stand-in for pymongo's ``Database.command`` (readiness ping)."""
        return {"ok": 1}


class FakeMongoClient:
    """Drop-in replacement for ``pymongo.MongoClient`` in ``create_app``."""

    def __init__(self) -> None:
        self._database = FakeDatabase()

    def get_database(self, name: str | None = None) -> FakeDatabase:
        return self._database
