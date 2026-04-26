"""Tests for poller dispatcher business logic."""

from unittest.mock import Mock, patch

import pytest

from services.alert_dispatcher import create_app
from services.alert_dispatcher.extensions import db
from services.alert_dispatcher.init_db import _seed_webhooks
from services.alert_dispatcher.models import Delivery, Webhook
from services.alert_dispatcher.poller.dispatcher import poll_and_dispatch_alerts


@pytest.fixture()
def service_app(tmp_path):
    """Create an isolated app backed by a temporary SQLite file."""
    db_file = tmp_path / "alert_dispatcher_services_test.db"
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


def test_poll_and_dispatch_creates_successful_delivery(service_app, monkeypatch):
    """A new unresolved alert calls delivery API and increments created count."""
    monkeypatch.setenv("ALERT_DISPATCHER_BASE_URL", "http://dispatcher:5002")
    with service_app.app_context(), patch(
        "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
        return_value=[
            {
                "alert_id": 1001,
                "shipment_id": 501,
                "severity": "critical",
                "message": "Temperature out of range",
            }
        ],
    ), patch(
        "services.alert_dispatcher.poller.dispatcher.requests.post",
        return_value=Mock(status_code=201, text="created"),
    ) as mock_post:
        summary = poll_and_dispatch_alerts()

    assert summary == {
        "fetched_alerts": 1,
        "active_webhooks": 1,
        "created_deliveries": 1,
        "skipped_duplicates": 0,
    }
    assert mock_post.call_count == 1
    assert mock_post.call_args.kwargs["timeout"] == 5.0
    assert mock_post.call_args.kwargs["json"]["status"] == "sent"
    assert mock_post.call_args.args[0] == "http://dispatcher:5002/deliveries"


def test_poll_and_dispatch_skips_existing_duplicate(service_app):
    """Existing (alert_id, webhook_id) delivery is skipped and not resent."""
    with service_app.app_context():
        webhook = Webhook.query.filter_by(status=0).first()
        assert webhook is not None

        existing = Delivery(
            alert_id=2002,
            shipment_id=9001,
            webhook_id=webhook.id,
            target_url=webhook.target_url,
            status="sent",
            response_code=200,
            error_message=None,
            attempt_count=1,
        )
        db.session.add(existing)
        db.session.commit()

        with patch(
            "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
            return_value=[
                {"alert_id": 2002, "shipment_id": 9001, "message": "Duplicate alert"}
            ],
        ), patch("services.alert_dispatcher.poller.dispatcher.send_webhook") as mock_sender, patch(
            "services.alert_dispatcher.poller.dispatcher.requests.post"
        ) as mock_post:
            summary = poll_and_dispatch_alerts()

    assert summary == {
        "fetched_alerts": 1,
        "active_webhooks": 1,
        "created_deliveries": 0,
        "skipped_duplicates": 1,
    }
    with service_app.app_context():
        assert Delivery.query.filter_by(
            alert_id=2002,
            shipment_id=9001,
            webhook_id=webhook.id,
        ).count() == 1
    mock_sender.assert_not_called()
    mock_post.assert_not_called()


def test_poll_and_dispatch_records_failed_for_non_2xx(service_app):
    """Non-2xx webhook send response is posted as failed delivery."""
    with service_app.app_context(), patch(
        "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
        return_value=[{"alert_id": 3003, "shipment_id": 7003, "message": "Any message"}],
    ), patch("services.alert_dispatcher.poller.dispatcher.send_webhook", return_value=503), patch(
        "services.alert_dispatcher.poller.dispatcher.requests.post",
        return_value=Mock(status_code=201, text="created"),
    ) as mock_post:
        summary = poll_and_dispatch_alerts()

    assert summary == {
        "fetched_alerts": 1,
        "active_webhooks": 1,
        "created_deliveries": 1,
        "skipped_duplicates": 0,
    }
    assert mock_post.call_count == 1
    assert mock_post.call_args.kwargs["json"]["status"] == "failed"
    assert mock_post.call_args.kwargs["json"]["response_code"] == 503


def test_poll_and_dispatch_handles_alert_without_shipment_id(service_app):
    """Alerts without shipment_id are still dispatched."""
    with service_app.app_context(), patch(
        "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
        return_value=[{"alert_id": 4004, "shipment_id": None, "message": "No shipment context"}],
    ), patch(
        "services.alert_dispatcher.poller.dispatcher.requests.post",
        return_value=Mock(status_code=201, text="created"),
    ) as mock_post:
        summary = poll_and_dispatch_alerts()

    assert summary == {
        "fetched_alerts": 1,
        "active_webhooks": 1,
        "created_deliveries": 1,
        "skipped_duplicates": 0,
    }
    assert mock_post.call_args.kwargs["json"]["shipment_id"] is None


def test_poll_and_dispatch_raises_when_delivery_api_fails(service_app):
    """Unexpected delivery API response code raises RuntimeError."""
    with service_app.app_context(), patch(
        "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
        return_value=[{"alert_id": 5005, "shipment_id": 1005}],
    ), patch(
        "services.alert_dispatcher.poller.dispatcher.requests.post",
        return_value=Mock(status_code=500, text="server error"),
    ):
        with pytest.raises(RuntimeError):
            poll_and_dispatch_alerts()


def test_poll_and_dispatch_skips_alert_without_alert_id(service_app):
    """Alerts missing alert_id are ignored before webhook and delivery calls."""
    with service_app.app_context(), patch(
        "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
        return_value=[{"shipment_id": 123, "message": "missing alert id"}],
    ), patch("services.alert_dispatcher.poller.dispatcher.send_webhook") as mock_sender, patch(
        "services.alert_dispatcher.poller.dispatcher.requests.post"
    ) as mock_post:
        summary = poll_and_dispatch_alerts()

    assert summary == {
        "fetched_alerts": 1,
        "active_webhooks": 1,
        "created_deliveries": 0,
        "skipped_duplicates": 0,
    }
    mock_sender.assert_not_called()
    mock_post.assert_not_called()


def test_poll_and_dispatch_counts_delivery_api_duplicate_as_skipped(service_app):
    """Delivery API returning 200 is counted as skipped duplicate."""
    with service_app.app_context(), patch(
        "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
        return_value=[{"alert_id": 6006, "shipment_id": 16006}],
    ), patch(
        "services.alert_dispatcher.poller.dispatcher.Delivery.query"
    ) as mock_query, patch(
        "services.alert_dispatcher.poller.dispatcher.requests.post",
        return_value=Mock(status_code=200, text="duplicate"),
    ):
        mock_query.filter_by.return_value.first.return_value = None
        summary = poll_and_dispatch_alerts()

    assert summary == {
        "fetched_alerts": 1,
        "active_webhooks": 1,
        "created_deliveries": 0,
        "skipped_duplicates": 1,
    }
