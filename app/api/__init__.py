from flask import Blueprint
from .auth import auth_bp
from .users import users_bp
from .tasks import tasks_bp
from .subtasks import subtasks_bp
from .notifications import notifications_bp
from .planner import planner_bp
from .summaries import summaries_bp

def init_api(app):
    # Inject app.db into blueprints
    auth_bp.db = app.db
    users_bp.db = app.db
    tasks_bp.db = app.db
    subtasks_bp.db = app.db
    notifications_bp.db = app.db
    planner_bp.db = app.db
    summaries_bp.db = app.db

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(subtasks_bp, url_prefix="/api/subtasks")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(planner_bp, url_prefix="/api/planner")
    app.register_blueprint(summaries_bp, url_prefix="/api/summaries")