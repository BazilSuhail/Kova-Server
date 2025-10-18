"""Blueprint registration — the only place where URL prefixes are defined.

Prefixes are part of the public contract and must stay byte-for-byte stable.
"""
from __future__ import annotations

from flask import Flask

from .auth import auth_bp
from .calendar import calendar_bp
from .daily_recap import daily_recap_bp
from .dashboard import dashboard_bp
from .devices import devices_bp
from .health import health_bp
from .mood import mood_bp
from .notifications import notifications_bp
from .planner import planner_bp
from .progress import progress_bp
from .reflections import reflections_bp
from .reminders import reminders_bp
from .subtasks import subtasks_bp
from .suggestions import suggestions_bp
from .summaries import summaries_bp
from .sync import sync_bp
from .tasks import tasks_bp
from .users import users_bp
from .weekly_recap import weekly_recap_bp


def register_blueprints(app: Flask) -> None:
    """Mount every route module on the app."""
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(subtasks_bp, url_prefix="/api/subtasks")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(planner_bp, url_prefix="/api/planner")
    app.register_blueprint(summaries_bp, url_prefix="/api/summaries")
    app.register_blueprint(daily_recap_bp, url_prefix="/api/daily-recap")
    app.register_blueprint(weekly_recap_bp, url_prefix="/api/weekly-recap")
    # --- Life-assistant surfaces (Sprint F) ---
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(calendar_bp, url_prefix="/api/calendar")
    app.register_blueprint(mood_bp, url_prefix="/api/mood")
    app.register_blueprint(reflections_bp, url_prefix="/api/reflections")
    app.register_blueprint(progress_bp, url_prefix="/api/progress")
    app.register_blueprint(suggestions_bp, url_prefix="/api/suggestions")
    app.register_blueprint(devices_bp, url_prefix="/api/devices")
    app.register_blueprint(reminders_bp, url_prefix="/api/reminders")
    app.register_blueprint(sync_bp, url_prefix="/api/sync")
    # Health probes live directly under /api (public, no version prefix).
    app.register_blueprint(health_bp, url_prefix="/api")
