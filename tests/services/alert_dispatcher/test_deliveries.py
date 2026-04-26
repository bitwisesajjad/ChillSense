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
            shipment_id=5001,
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
            shipment_id=5002,
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
        "shipment_id",
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
    assert data[0]["shipment_id"] == 5002
    assert data[0]["status"] == "sent"
    assert data[0]["response_code"] == 200
    assert data[0]["error_message"] is None
    assert data[0]["attempt_count"] == 1

    assert data[1]["alert_id"] == 101
    assert data[1]["shipment_id"] == 5001
    assert data[1]["status"] == "failed"
    assert data[1]["response_code"] == 500
    assert data[1]["error_message"] == "timeout"
    assert data[1]["attempt_count"] == 2


def test_deliveries_post_creates_row_and_returns_location(delivery_client):
    """POST /deliveries creates a new delivery and returns 201 + Location."""
    payload = {
        "alert_id": 7001,
        "shipment_id": 9001,
        "webhook_id": 1,
        "target_url": "https://hooks.example.com/telegram",
        "status": "sent",
        "response_code": 200,
        "error_message": None,
        "attempt_count": 1,
    }

    resp = delivery_client.post("/deliveries", json=payload)

    assert resp.status_code == 201
    created = resp.get_json()
    assert created["alert_id"] == 7001
    assert created["shipment_id"] == 9001
    assert created["webhook_id"] == 1
    assert created["status"] == "sent"
    assert created["response_code"] == 200
    assert created["error_message"] is None
    assert created["attempt_count"] == 1
    assert resp.headers["Location"] == f"/deliveries/{created['id']}"


def test_deliveries_post_returns_existing_row_for_duplicate(delivery_client):
    """POST /deliveries returns existing row with 200 for duplicate key."""
    payload = {
        "alert_id": 7002,
        "shipment_id": 9002,
        "webhook_id": 1,
        "target_url": "https://hooks.example.com/telegram",
        "status": "failed",
        "response_code": 503,
        "error_message": "service unavailable",
        "attempt_count": 1,
    }

    first = delivery_client.post("/deliveries", json=payload)
    second = delivery_client.post("/deliveries", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.get_json()["id"] == first.get_json()["id"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"alert_id": 1, "webhook_id": 1, "target_url": "x", "status": "queued"},
        {"alert_id": "1", "webhook_id": 1, "target_url": "x", "status": "sent"},
        {
            "alert_id": 1,
            "webhook_id": 1,
            "target_url": "x",
            "status": "sent",
            "unexpected": True,
        },
    ],
)
def test_deliveries_post_rejects_invalid_payloads(delivery_client, payload):
    """POST /deliveries validates allowed fields and field value types."""
    resp = delivery_client.post("/deliveries", json=payload)

    assert resp.status_code == 400


def test_deliveries_post_rejects_non_json_body(delivery_client):
    """POST /deliveries returns 415 when request body is not JSON."""
    resp = delivery_client.post("/deliveries", data="not-json", content_type="text/plain")

    assert resp.status_code == 415


@pytest.mark.parametrize(
    "payload",
    [
        {
            "alert_id": 1,
            "shipment_id": "9001",
            "webhook_id": 1,
            "target_url": "https://hooks.example.com/x",
            "status": "sent",
        },
        {
            "alert_id": 1,
            "webhook_id": "1",
            "target_url": "https://hooks.example.com/x",
            "status": "sent",
        },
        {
            "alert_id": 1,
            "webhook_id": 1,
            "target_url": "   ",
            "status": "sent",
        },
        {
            "alert_id": 1,
            "webhook_id": 1,
            "target_url": "https://hooks.example.com/x",
            "status": "sent",
            "response_code": "200",
        },
        {
            "alert_id": 1,
            "webhook_id": 1,
            "target_url": "https://hooks.example.com/x",
            "status": "sent",
            "error_message": 123,
        },
        {
            "alert_id": 1,
            "webhook_id": 1,
            "target_url": "https://hooks.example.com/x",
            "status": "sent",
            "attempt_count": 0,
        },
    ],
)
def test_deliveries_post_rejects_invalid_field_types(delivery_client, payload):
    """POST /deliveries rejects invalid optional field types and values."""
    resp = delivery_client.post("/deliveries", json=payload)

    assert resp.status_code == 400
