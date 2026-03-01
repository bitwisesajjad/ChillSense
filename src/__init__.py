"""Application factory for API."""

import os
from flask import Flask, jsonify
from .api import api_bp, ShipmentConverter, ReadingConverter
from .extensions import db

def create_app(test_config=None):
    """Create and configure the flask app."""
    app = Flask(__name__)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config is not None:
        app.config.update(test_config)
    else:
        user = os.getenv("POSTGRES_USER", "user")
        pw = os.getenv("POSTGRES_PASSWORD", "password")
        host = os.getenv("POSTGRES_HOST", "postgres-db")
        db_name = os.getenv("POSTGRES_DB", "coldchain")
        port = os.getenv("POSTGRES_PORT", "5432")

        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql://{user}:{pw}@{host}:{port}/{db_name}"
            )

    db.init_app(app)

    app.url_map.converters["shipment"] = ShipmentConverter
    app.url_map.converters["reading"] = ReadingConverter

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/health")
    def health():
        """Simple health check endpoint."""
        return jsonify({"status": "ok"})

    return app
