"""
Pytest fixtures for ChillSense functional API tests.
"""

import pytest
from src import create_app
from src.extensions import db
from src.models import ApiKey

@pytest.fixture()
def app():
    """Create and configure a Flask application for tests."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    with app.app_context():
        db.create_all()
        admin_key = ApiKey(key=ApiKey.key_hash("adminkey"), admin=True)
        db.session.add(admin_key)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    """Return a Flask test client for sending requests to API."""
    return app.test_client()
