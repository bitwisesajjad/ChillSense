"""Tests for alert-dispatcher webhooks endpoint."""

import pytest

from services.alert_dispatcher import create_app
from services.alert_dispatcher.extensions import db
from services.alert_dispatcher.init_db import _seed_webhooks


@pytest.fixture()
def webhook_app(tmp_path):
    """Create an isolated app backed by a temporary SQLite file."""
    db_file = tmp_path / "alert_dispatcher_test.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        }
    )

    with app.app_context():
        db.create_all()
        _seed_webhooks()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def webhook_client(webhook_app):
    """Return a test client for webhook endpoint tests."""
    return webhook_app.test_client()


def test_webhooks_get_returns_seeded_rows(webhook_client):
    """GET /webhooks returns the seeded webhook rows."""
    resp = webhook_client.get("/webhooks")

    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2

    names = {row["name"] for row in data}
    assert names == {"telegram", "email"}


def test_webhooks_get_response_structure(webhook_client):
    """GET /webhooks returns required response fields for each row."""
    resp = webhook_client.get("/webhooks")

    assert resp.status_code == 200
    data = resp.get_json()

    required_fields = {
        "id",
        "name",
        "target_url",
        "status",
        "created_at",
        "updated_at",
    }

    for row in data:
        assert set(row.keys()) == required_fields
        assert isinstance(row["id"], int)
        assert isinstance(row["name"], str)
        assert isinstance(row["target_url"], str)
        assert isinstance(row["status"], int)
        assert isinstance(row["created_at"], str)
        assert isinstance(row["updated_at"], str)
