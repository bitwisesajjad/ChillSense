"""Create SQLite tables and seed initial webhook data for alert dispatcher."""

from pathlib import Path

from flask import Flask

from .extensions import db
from .models import Webhook


def _create_app():
    """Create a minimal Flask app for DB initialization."""
    app = Flask(__name__)
    db_file = Path(__file__).resolve().parent / "alert_dispatcher.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_file}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _seed_webhooks():
    """Seed hardcoded webhook rows if they are missing."""
    rows = [
        {
            "name": "telegram",
            "target_url": "https://api.telegram.org/bot<token>/sendMessage",
            "status": 0,
        },
        {
            "name": "email",
            "target_url": "https://mailer.internal.local/send",
            "status": 1,
        },
    ]

    for row in rows:
        existing = Webhook.query.filter_by(name=row["name"]).first()
        if existing is None:
            db.session.add(Webhook(**row))

    db.session.commit()


def init_db():
    """Create tables and seed initial data."""
    app = _create_app()
    with app.app_context():
        db.create_all()
        _seed_webhooks()
    print("alert-dispatcher database initialized")


if __name__ == "__main__":
    init_db()
