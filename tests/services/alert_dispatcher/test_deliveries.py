"""Tests for alert-dispatcher deliveries endpoint."""

from datetime import datetime, timedelta

import pytest

from services.alert_dispatcher import create_app
from services.alert_dispatcher.extensions import db
from services.alert_dispatcher.init_db import _seed_webhooks
from services.alert_dispatcher.models import Delivery, Webhook


@pytest.fixture()
def delivery_app(tmp_path):
    """Create an isolated app backed by a temporary SQLite file."""
    db_file = tmp_path / "alert_dispatcher_delivery_test.db"
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
def delivery_client(delivery_app):
    """Return a test client for delivery endpoint tests."""
    return delivery_app.test_client()


def test_deliveries_get_returns_empty_list_initially(delivery_client):
    """GET /deliveries returns an empty list when no rows exist."""
    resp = delivery_client.get("/deliveries")

    assert resp.status_code == 200
    assert resp.get_json() == []


def test_deliveries_get_returns_inserted_rows_correctly(delivery_app, delivery_client):
    """GET /deliveries returns manually inserted delivery rows in newest-first order."""
    with delivery_app.app_context():
        webhook = Webhook.query.filter_by(name="telegram").first()
        assert webhook is not None

        older = Delivery(
            alert_id=101,
            webhook_id=webhook.id,
            target_url="https://hooks.example.com/telegram",
            status="failed",
            response_code=500,
            error_message="timeout",
            attempt_count=2,
            created_at=datetime.utcnow() - timedelta(minutes=5),
        )
        newer = Delivery(
            alert_id=102,
            webhook_id=webhook.id,
            target_url="https://hooks.example.com/telegram",
            status="sent",
            response_code=200,
            error_message=None,
            attempt_count=1,
            created_at=datetime.utcnow(),
        )
        db.session.add_all([older, newer])
        db.session.commit()

    resp = delivery_client.get("/deliveries")

    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2

    required_fields = {
        "id",
        "alert_id",
        "webhook_id",
        "target_url",
        "status",
        "response_code",
        "error_message",
        "attempt_count",
        "created_at",
    }

    for row in data:
        assert set(row.keys()) == required_fields

    # Newest row should come first.
    assert data[0]["alert_id"] == 102
    assert data[0]["status"] == "sent"
    assert data[0]["response_code"] == 200
    assert data[0]["error_message"] is None
    assert data[0]["attempt_count"] == 1

    assert data[1]["alert_id"] == 101
    assert data[1]["status"] == "failed"
    assert data[1]["response_code"] == 500
    assert data[1]["error_message"] == "timeout"
    assert data[1]["attempt_count"] == 2
