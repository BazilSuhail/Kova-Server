"""MongoDB connection and index management (I/O lives here, not in the factory)."""
from __future__ import annotations

import logging

from flask import Flask
from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)


def connect_mongo(mongo_uri: str) -> MongoClient:
    """Open a client and fail fast when the cluster is unreachable.

    The 5s server-selection timeout is kept from the legacy factory so deploys
    still fail fast instead of hanging.  The URI itself is never logged — it
    can embed credentials.
    """
    client: MongoClient = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    logger.info("mongodb connected")
    return client


def init_db(app: Flask, client: MongoClient) -> Database:
    """Attach the default database to the app and ensure indexes exist."""
    db = client.get_database()
    # Flask has no declared ``db`` attribute; the dynamic attach is the point.
    app.db = db  # type: ignore[attr-defined]  # kept for code reading ``app.db``
    create_indexes(db)
    return db


def create_indexes(db: Database) -> None:
    """Create the indexes the API relies on; idempotent, raises on failure.

    Unique indexes are load-bearing: they enforce userId/email/taskId/...
    uniqueness that application code also checks for friendlier errors.
    """
    db.users.create_index([("userId", 1)], unique=True)
    db.users.create_index([("email", 1)], unique=True)
    db.tasks.create_index([("taskId", 1)], unique=True)
    db.tasks.create_index([("userId", 1)])
    db.subtasks.create_index([("subtaskId", 1)], unique=True)
    db.subtasks.create_index([("taskId", 1)])
    db.notifications.create_index([("notificationId", 1)], unique=True)
    db.notifications.create_index([("userId", 1)])
    db.planner.create_index([("plannerId", 1)], unique=True)
    db.planner.create_index([("userId", 1)])
    db.planner.create_index([("date", 1)])
    db.summaries.create_index([("summaryId", 1)], unique=True)
    db.summaries.create_index([("userId", 1)])
    # Logout revocation: unique jti for O(1) checks, TTL to self-purge dead rows.
    db.token_blocklist.create_index([("jti", 1)], unique=True)
    db.token_blocklist.create_index([("expiresAt", 1)], expireAfterSeconds=0)
    logger.info("mongodb indexes ensured")
