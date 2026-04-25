"""Tests for poller dispatcher business logic."""

from unittest.mock import patch

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


def test_poll_and_dispatch_creates_successful_delivery(service_app):
    """A new unresolved alert creates a sent delivery for each active webhook."""
    with service_app.app_context():
        with patch(
            "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
            return_value=[
                {
                    "alert_id": 1001,
                    "shipment_id": 501,
                    "severity": "critical",
                    "message": "Temperature out of range",
                }
            ],
        ):
            summary = poll_and_dispatch_alerts()

        row = Delivery.query.filter_by(alert_id=1001).one()

        assert summary == {
            "fetched_alerts": 1,
            "active_webhooks": 1,
            "created_deliveries": 1,
            "skipped_duplicates": 0,
        }
        assert row.status == "sent"
        assert row.shipment_id == 501
        assert row.response_code == 200
        assert row.error_message is None
        assert row.attempt_count == 1


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
        ), patch("services.alert_dispatcher.poller.dispatcher.send_webhook") as mock_sender:
            summary = poll_and_dispatch_alerts()

        assert summary == {
            "fetched_alerts": 1,
            "active_webhooks": 1,
            "created_deliveries": 0,
            "skipped_duplicates": 1,
        }
        assert Delivery.query.filter_by(
            alert_id=2002,
            shipment_id=9001,
            webhook_id=webhook.id,
        ).count() == 1
        mock_sender.assert_not_called()


def test_poll_and_dispatch_records_failed_for_non_2xx(service_app):
    """Non-2xx fake sender response is persisted as failed delivery."""
    with service_app.app_context():
        with patch(
            "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
            return_value=[{"alert_id": 3003, "shipment_id": 7003, "message": "Any message"}],
        ), patch("services.alert_dispatcher.poller.dispatcher.send_webhook", return_value=503):
            summary = poll_and_dispatch_alerts()

        row = Delivery.query.filter_by(alert_id=3003).one()

        assert summary == {
            "fetched_alerts": 1,
            "active_webhooks": 1,
            "created_deliveries": 1,
            "skipped_duplicates": 0,
        }
        assert row.status == "failed"
        assert row.shipment_id == 7003
        assert row.response_code == 503
        assert row.error_message is None
        assert row.attempt_count == 1


def test_poll_and_dispatch_handles_alert_without_shipment_id(service_app):
    """Alerts without shipment_id are still dispatched and persisted."""
    with service_app.app_context():
        with patch(
            "services.alert_dispatcher.poller.dispatcher.fetch_active_alerts",
            return_value=[{"alert_id": 4004, "shipment_id": None, "message": "No shipment context"}],
        ):
            summary = poll_and_dispatch_alerts()

        row = Delivery.query.filter_by(alert_id=4004).one()

        assert summary == {
            "fetched_alerts": 1,
            "active_webhooks": 1,
            "created_deliveries": 1,
            "skipped_duplicates": 0,
        }
        assert row.shipment_id is None
