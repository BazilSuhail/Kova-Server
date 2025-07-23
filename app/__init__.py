from flask import Flask
from .config import Config
from .extensions import mongo, jwt
from .routes.auth import auth_bp
from .routes.user import user_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")

    return app
