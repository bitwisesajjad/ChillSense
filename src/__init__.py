"""Application factory for API."""
import os
from flask import Flask, jsonify
from .extensions import db

def create_app():
    """Create and configure the flask app."""
    app = Flask(__name__)
    user = os.getenv("POSTGRES_USER", "user")
    pw = os.getenv("POSTGRES_PASSWORD", "password")
    host = os.getenv("POSTGRES_HOST", "postgres-db")
    db_name = os.getenv("POSTGRES_DB", "coldchain")
    port = os.getenv("POSTGRES_PORT", "5432")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{user}:{pw}"
        f"@{host}:{port}/{db_name}"
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/health")
    def health():
        """Simple health check endpoint."""
        return jsonify({"status": "ok"})

    return app
