import os

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/task_management")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")