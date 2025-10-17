"""Blueprint registration — the only place where URL prefixes are defined.

Prefixes are part of the public contract and must stay byte-for-byte stable.
"""
from __future__ import annotations

from flask import Flask

from .auth import auth_bp
from .daily_recap import daily_recap_bp
from .notifications import notifications_bp
from .planner import planner_bp
from .subtasks import subtasks_bp
from .summaries import summaries_bp
from .tasks import tasks_bp
from .users import users_bp


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
