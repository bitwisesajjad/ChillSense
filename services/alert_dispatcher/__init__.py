"""Application factory for alert-dispatcher service."""

import os
from pathlib import Path

from flask import Flask, send_file
from flask_swagger_ui import get_swaggerui_blueprint

from .api import api_bp
from .extensions import db


def create_app(test_config=None):
    """Create and configure alert-dispatcher Flask app."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config is not None:
        app.config.update(test_config)
    else:
        db_file = Path(__file__).resolve().parent / "alert_dispatcher.db"
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_file}"

    db.init_app(app)
    app.register_blueprint(api_bp)

    # Keep Swagger UI auto-enabled only in development/debug mode.
    if (
        app.debug
        or app.config.get("DEBUG")
        or os.environ.get("FLASK_DEBUG") == "1"
        or app.config.get("ENABLE_SWAGGER_UI") is True
    ):
        swaggerui_bp = get_swaggerui_blueprint(
            "/apidocs",
            "/openapi.yaml",
            config={"app_name": "Alert Dispatcher API"},
        )
        app.register_blueprint(swaggerui_bp, url_prefix="/apidocs")

        @app.route("/openapi.yaml")
        def openapi_spec():
            """Serve OpenAPI spec used by Swagger UI."""
            service_root = Path(__file__).resolve().parent
            return send_file(service_root / "openapi.yaml", mimetype="application/yaml")

    return app

# FLASK_DEBUG=1 FLASK_APP=services.alert_dispatcher flask run --port 5002
# http://localhost:5002/webhooks
# http://localhost:5002/apidocs/