"""Service container: composed once at startup, read per request by routes.

Replaces the legacy pattern of monkey-patching ``blueprint.db = app.db`` at
registration time, which coupled every route to bootstrap order and made the
blueprints untestable in isolation.  Routes now call :func:`get_services`.
"""
from __future__ import annotations

from dataclasses import dataclass

from flask import current_app
from pymongo.database import Database

from ..repositories import (
    NotificationRepository,
    PlannerRepository,
    SubtaskRepository,
    SummaryRepository,
    TaskRepository,
    UserRepository,
)
from .auth_service import AuthService
from .daily_recap_service import DailyRecapService
from .notification_service import NotificationService
from .planner_service import PlannerService
from .subtask_service import SubtaskService
from .summary_service import SummaryService
from .task_service import TaskService
from .user_service import UserService

# Key under which the container lives in ``app.extensions``.
EXTENSION_KEY = "zenflow.services"


@dataclass(frozen=True)
class Services:
    """Immutable set of application services (one instance per process)."""

    auth: AuthService
    users: UserService
    tasks: TaskService
    subtasks: SubtaskService
    notifications: NotificationService
    planner: PlannerService
    summaries: SummaryService
    daily_recap: DailyRecapService


def build_services(db: Database) -> Services:
    """Wire repositories into services — the app's single composition root."""
    users = UserRepository(db)
    tasks = TaskRepository(db)
    return Services(
        auth=AuthService(users),
        users=UserService(users),
        tasks=TaskService(tasks, SubtaskRepository(db)),
        subtasks=SubtaskService(SubtaskRepository(db), tasks),
        notifications=NotificationService(NotificationRepository(db)),
        planner=PlannerService(PlannerRepository(db), tasks),
        summaries=SummaryService(SummaryRepository(db)),
        daily_recap=DailyRecapService(tasks, PlannerRepository(db)),
    )


def get_services() -> Services:
    """Fetch the container for the running app (call inside a request context)."""
    return current_app.extensions[EXTENSION_KEY]
