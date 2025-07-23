from flask import Flask
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
from .config import Config
from .api import init_api

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config.from_object(Config)

    # Initialize MongoDB
    client = MongoClient(app.config["MONGO_URI"])
    app.db = client.get_database()

    # Create indexes
    app.db.users.create_index([("userId", 1)], unique=True)
    app.db.users.create_index([("email", 1)], unique=True)
    app.db.tasks.create_index([("taskId", 1)], unique=True)
    app.db.tasks.create_index([("userId", 1)])
    app.db.subtasks.create_index([("subtaskId", 1)], unique=True)
    app.db.subtasks.create_index([("taskId", 1)])
    app.db.notifications.create_index([("notificationId", 1)], unique=True)
    app.db.notifications.create_index([("userId", 1)])
    app.db.planner.create_index([("plannerId", 1)], unique=True)
    app.db.planner.create_index([("userId", 1)])
    app.db.planner.create_index([("date", 1)])
    app.db.summaries.create_index([("summaryId", 1)], unique=True)
    app.db.summaries.create_index([("userId", 1)])

    # Initialize JWT
    JWTManager(app)

    # Enable CORS
    CORS(app)

    # Register API blueprints
    init_api(app)

    return app
# from flask import Flask
# from flask_jwt_extended import JWTManager
# from pymongo import MongoClient
# from flask_cors import CORS
# from dotenv import load_dotenv
# from .config import Config
# from .api import init_api

# def create_app():
#     app = Flask(__name__)
#     load_dotenv()
#     app.config.from_object(Config)

#     # Initialize MongoDB
#     client = MongoClient(app.config["MONGO_URI"])
#     app.db = client.get_database()

#     # Create indexes
#     app.db.users.create_index([("userId", 1)], unique=True)
#     app.db.users.create_index([("email", 1)], unique=True)
#     app.db.tasks.create_index([("taskId", 1)], unique=True)
#     app.db.tasks.create_index([("userId", 1)])
#     app.db.subtasks.create_index([("subtaskId", 1)], unique=True)
#     app.db.subtasks.create_index([("taskId", 1)])
#     app.db.notifications.create_index([("notificationId", 1)], unique=True)
#     app.db.notifications.create_index([("userId", 1)])
#     app.db.planner.create_index([("plannerId", 1)], unique=True)
#     app.db.planner.create_index([("userId", 1)])
#     app.db.planner.create_index([("date", 1)])
#     app.db.summaries.create_index([("summaryId", 1)], unique=True)
#     app.db.summaries.create_index([("userId", 1)])

#     # Initialize JWT
#     JWTManager(app)

#     # Enable CORS
#     CORS(app)

#     # Register API blueprints
#     init_api(app)

#     return app