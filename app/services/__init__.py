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
    DeviceRepository,
    MoodRepository,
    NotificationRepository,
    PlannerRepository,
    ReflectionRepository,
    ReminderRepository,
    SubtaskRepository,
    SummaryRepository,
    TaskRepository,
    TokenBlocklistRepository,
    TombstoneRepository,
    UserRepository,
)
from .auth_service import AuthService
from .calendar_service import CalendarService
from .daily_recap_service import DailyRecapService
from .dashboard_service import DashboardService
from .device_service import DeviceService
from .mood_service import MoodService
from .notification_service import NotificationService
from .planner_service import PlannerService
from .progress_service import ProgressService
from .reflection_service import ReflectionService
from .reminder_service import ReminderService
from .subtask_service import SubtaskService
from .suggestion_service import SuggestionService
from .summary_service import SummaryService
from .sync_service import SyncService
from .task_service import TaskService
from .user_service import UserService
from .weekly_recap_service import WeeklyRecapService

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
    weekly_recap: WeeklyRecapService
    moods: MoodService
    reflections: ReflectionService
    progress: ProgressService
    suggestions: SuggestionService
    devices: DeviceService
    reminders: ReminderService
    dashboard: DashboardService
    sync: SyncService
    calendar: CalendarService


def build_services(db: Database) -> Services:
    """Wire repositories into services — the app's single composition root."""
    users = UserRepository(db)
    tasks = TaskRepository(db)
    subtasks = SubtaskRepository(db)
    planners = PlannerRepository(db)
    summaries = SummaryRepository(db)
    notifications = NotificationRepository(db)
    moods = MoodRepository(db)
    reflections = ReflectionRepository(db)
    devices = DeviceRepository(db)
    reminders = ReminderRepository(db)
    tombstones = TombstoneRepository(db)
    blocklist = TokenBlocklistRepository(db)

    notification_service = NotificationService(notifications, tombstones)
    progress = ProgressService(tasks, moods, reflections)
    suggestions = SuggestionService(tasks, moods, reflections, reminders)

    return Services(
        auth=AuthService(users, blocklist),
        users=UserService(
            users,
            tasks,
            subtasks,
            planners,
            summaries,
            notifications,
            moods,
            reflections,
            devices,
            reminders,
            tombstones,
            blocklist,
        ),
        tasks=TaskService(tasks, subtasks, tombstones),
        subtasks=SubtaskService(subtasks, tasks, tombstones),
        notifications=notification_service,
        planner=PlannerService(planners, tasks, tombstones),
        summaries=SummaryService(summaries, tasks, tombstones),
        daily_recap=DailyRecapService(tasks, planners),
        weekly_recap=WeeklyRecapService(tasks, planners),
        moods=MoodService(moods, tombstones),
        reflections=ReflectionService(reflections, tombstones),
        progress=progress,
        suggestions=suggestions,
        devices=DeviceService(devices),
        reminders=ReminderService(
            reminders, devices, notification_service, tombstones
        ),
        dashboard=DashboardService(
            tasks, notifications, reminders, moods, summaries, progress, suggestions
        ),
        sync=SyncService(
            tasks,
            subtasks,
            planners,
            summaries,
            notifications,
            moods,
            reflections,
            reminders,
            tombstones,
        ),
        calendar=CalendarService(tasks, planners),
    )


def get_services() -> Services:
    """Fetch the container for the running app (call inside a request context)."""
    return current_app.extensions[EXTENSION_KEY]
