from flask import Flask
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
import os
from .config import Config
from .api.users import users_bp
from .api.tasks import tasks_bp
from .api.subtasks import subtasks_bp
from .api.notifications import notifications_bp
from .api.planner import planner_bp
from .api.summaries import summaries_bp

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object(Config)

    # Initialize MongoDB
    client = MongoClient(app.config["MONGO_URI"])
    app.db = client.get_database()

    # Initialize JWT
    jwt = JWTManager(app)

    # Enable CORS (optional)
    CORS(app)

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(subtasks_bp, url_prefix="/api/subtasks")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(planner_bp, url_prefix="/api/planner")
    app.register_blueprint(summaries_bp, url_prefix="/api/summaries")

    return app