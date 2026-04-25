"""Core polling and dispatching logic for alert-dispatcher service."""

from .chillsense_client import fetch_active_alerts
from ..extensions import db
from ..models import Delivery, Webhook


def send_webhook(url, payload):
    """Mock webhook sender used in this implementation step."""
    print("FAKE SEND:", url, payload)
    return 200


def poll_and_dispatch_alerts():
    """Fetch alerts and create delivery attempts for active webhooks."""
    alerts = fetch_active_alerts()
    active_webhooks = Webhook.query.filter_by(status=0).order_by(Webhook.id.asc()).all()

    created_deliveries = 0
    skipped_duplicates = 0

    for alert in alerts:
        alert_id = alert.get("alert_id")
        shipment_id = alert.get("shipment_id")
        if alert_id is None:
            continue

        payload = {"alert_id": alert_id}
        if alert.get("shipment_id") is not None:
            payload["shipment_id"] = alert.get("shipment_id")
        if alert.get("severity") is not None:
            payload["severity"] = alert.get("severity")
        if alert.get("message") is not None:
            payload["message"] = alert.get("message")

        for webhook in active_webhooks:
            duplicate = Delivery.query.filter_by(
                alert_id=alert_id,
                shipment_id=shipment_id,
                webhook_id=webhook.id,
            ).first()
            if duplicate is not None:
                skipped_duplicates += 1
                continue

            response_code = send_webhook(webhook.target_url, payload)
            status = "sent" if 200 <= response_code < 300 else "failed"

            delivery = Delivery(
                alert_id=alert_id,
                shipment_id=shipment_id,
                webhook_id=webhook.id,
                target_url=webhook.target_url,
                status=status,
                response_code=response_code,
                error_message=None,
                attempt_count=1,
            )
            db.session.add(delivery)
            created_deliveries += 1

    db.session.commit()

    return {
        "fetched_alerts": len(alerts),
        "active_webhooks": len(active_webhooks),
        "created_deliveries": created_deliveries,
        "skipped_duplicates": skipped_duplicates,
    }
