import os
from pathlib import Path

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .config import CONFIG_BY_NAME, BaseConfig

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(BaseConfig)

    if test_config is not None:
        app.config.from_mapping(test_config)
    else:
        config_name = os.getenv("APP_ENV", "development")
        app.config.from_object(CONFIG_BY_NAME[config_name])

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from .auth import auth_bp
    from .views import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp)

    @app.get("/")
    def index():
        return jsonify(
            {
                "service": "DealRadar ingestion prototype",
                "role": "Python scraper and matching backend",
                "status": "ok",
            }
        )

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def handle_server_error(_error):
        return jsonify({"error": "Internal server error"}), 500

    return app
