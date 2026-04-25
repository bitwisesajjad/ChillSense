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


def test_webhooks_put_updates_status_inactive_to_active(webhook_client):
    """PUT /webhooks/<id> updates status from 1 to 0."""
    before_resp = webhook_client.get("/webhooks")
    before_data = before_resp.get_json()
    email_row = next(row for row in before_data if row["name"] == "email")

    assert email_row["status"] == 1
    before_updated_at = email_row["updated_at"]

    update_resp = webhook_client.put(
        f"/webhooks/{email_row['id']}",
        json={"status": 0},
    )

    assert update_resp.status_code == 200
    updated = update_resp.get_json()
    assert updated["id"] == email_row["id"]
    assert updated["name"] == "email"
    assert updated["status"] == 0
    assert updated["updated_at"] != before_updated_at


@pytest.mark.parametrize("payload", [{"status": 2}, {"status": -1}, {"status": "1"}])
def test_webhooks_put_rejects_invalid_status_values(webhook_client, payload):
    """PUT /webhooks/<id> rejects statuses outside allowed values."""
    resp = webhook_client.put("/webhooks/1", json=payload)

    assert resp.status_code == 400


def test_webhooks_put_returns_404_for_unknown_id(webhook_client):
    """PUT /webhooks/<id> returns 404 when webhook does not exist."""
    resp = webhook_client.put("/webhooks/99999", json={"status": 0})

    assert resp.status_code == 404


@pytest.mark.parametrize("payload", [{}, {"status": 0, "name": "telegram"}, None])
def test_webhooks_put_rejects_payload_with_missing_or_extra_fields(webhook_client, payload):
    """PUT /webhooks/<id> accepts only a single 'status' field."""
    resp = webhook_client.put("/webhooks/1", json=payload)

    assert resp.status_code == 400
