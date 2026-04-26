"""Tests for manual one-shot polling endpoint."""

# pylint: disable=redefined-outer-name

from unittest.mock import patch

import pytest

from services.alert_dispatcher import create_app
from services.alert_dispatcher.extensions import db
from services.alert_dispatcher.init_db import _seed_webhooks


@pytest.fixture(name="polling_app")
def fixture_polling_app(tmp_path):
    """Create an isolated app backed by a temporary SQLite file."""
    db_file = tmp_path / "alert_dispatcher_polling_test.db"
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


@pytest.fixture(name="polling_client")
def fixture_polling_client(polling_app):
    """Return a test client for polling-now endpoint tests."""
    return polling_app.test_client()


def test_polling_now_runs_dispatch_once_and_returns_summary(polling_client):
    """GET /polling-now executes one cycle and returns summary payload."""
    expected_summary = {
        "fetched_alerts": 2,
        "active_webhooks": 1,
        "created_deliveries": 2,
        "skipped_duplicates": 0,
    }

    with patch(
        "services.alert_dispatcher.resources.polling_now.poll_and_dispatch_alerts",
        return_value=expected_summary,
    ) as mock_poll:
        resp = polling_client.get("/polling-now")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Demo polling executed once"
    assert data["summary"] == expected_summary
    mock_poll.assert_called_once_with()


def test_polling_now_returns_502_when_dispatch_fails(polling_client):
    """GET /polling-now returns 502 if one-shot dispatch raises an error."""
    with patch(
        "services.alert_dispatcher.resources.polling_now.poll_and_dispatch_alerts",
        side_effect=RuntimeError("upstream timeout"),
    ):
        resp = polling_client.get("/polling-now")

    assert resp.status_code == 502
    assert "Polling failed" in resp.get_json()["message"]
