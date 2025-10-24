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
    logger.info("MongoDB connected")
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
    # Recap windows: daily/weekly dueDate range scans per user.
    db.tasks.create_index([("userId", 1), ("dueDate", 1)])
    db.subtasks.create_index([("subtaskId", 1)], unique=True)
    db.subtasks.create_index([("taskId", 1)])
    db.notifications.create_index([("notificationId", 1)], unique=True)
    db.notifications.create_index([("userId", 1)])
    # Feed listing sorts newest-first per user.
    db.notifications.create_index([("userId", 1), ("createdAt", -1)])
    db.planner.create_index([("plannerId", 1)], unique=True)
    db.planner.create_index([("userId", 1)])
    db.planner.create_index([("date", 1)])
    # Recap day lookups (prefix/range on date) scoped to a user.
    db.planner.create_index([("userId", 1), ("date", 1)])
    db.summaries.create_index([("summaryId", 1)], unique=True)
    db.summaries.create_index([("userId", 1)])
    # Logout revocation: unique jti for O(1) checks, TTL to self-purge dead rows.
    db.token_blocklist.create_index([("jti", 1)], unique=True)
    db.token_blocklist.create_index([("expiresAt", 1)], expireAfterSeconds=0)
    # --- Life-assistant collections (Sprint F) ---
    # Mood journal: newest-first feed + trend range scans per user.
    db.mood_entries.create_index([("moodId", 1)], unique=True)
    db.mood_entries.create_index([("userId", 1), ("loggedAt", -1)])
    # Daily reflections: one lookup per user/day.
    db.reflections.create_index([("reflectionId", 1)], unique=True)
    db.reflections.create_index([("userId", 1), ("date", 1)])
    # Push devices: a token identifies one device (moved, never duplicated).
    db.push_devices.create_index([("deviceId", 1)], unique=True)
    db.push_devices.create_index([("expoPushToken", 1)], unique=True)
    db.push_devices.create_index([("userId", 1)])
    # Reminders: due-scan by status+fireAt, owner listing.
    db.scheduled_reminders.create_index([("reminderId", 1)], unique=True)
    db.scheduled_reminders.create_index([("userId", 1)])
    db.scheduled_reminders.create_index([("status", 1), ("fireAt", 1)])
    # Offline sync: tombstones record deletions so clients can prune local rows.
    db.tombstones.create_index([("userId", 1), ("deletedAt", 1)])
    # Delta sync scans: (owner, updatedAt) per synced collection.
    db.tasks.create_index([("userId", 1), ("updatedAt", 1)])
    db.planner.create_index([("userId", 1), ("updatedAt", 1)])
    db.summaries.create_index([("userId", 1), ("updatedAt", 1)])
    db.notifications.create_index([("userId", 1), ("updatedAt", 1)])
    db.subtasks.create_index([("taskId", 1), ("updatedAt", 1)])
    logger.info("Database indexes ready")
