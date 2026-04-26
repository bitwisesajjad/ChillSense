"""Core polling and dispatching logic for alert-dispatcher service."""

import os

import requests

from .chillsense_client import fetch_active_alerts
from ..models import Delivery, Webhook


def send_webhook(url, payload):
    """Mock webhook sender used in this implementation step."""
    print("FAKE SEND:", url, payload)
    return 200


def poll_and_dispatch_alerts():
    """Fetch alerts and create delivery attempts for active webhooks."""
    alerts = fetch_active_alerts()
    base_url = os.getenv("ALERT_DISPATCHER_BASE_URL", "http://localhost:5002").rstrip("/")
    timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "5"))

    created_deliveries = 0
    skipped_duplicates = 0

    if not alerts:
        return {
            "fetched_alerts": 0,
            "active_webhooks": 0,
            "created_deliveries": 0,
            "skipped_duplicates": 0,
        }

    active_webhooks = Webhook.query.filter_by(status=0).order_by(Webhook.id.asc()).all()

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

            delivery_payload = {
                "alert_id": alert_id,
                "shipment_id": shipment_id,
                "webhook_id": webhook.id,
                "target_url": webhook.target_url,
                "status": status,
                "response_code": response_code,
                "error_message": None,
                "attempt_count": 1,
            }
            resp = requests.post(
                f"{base_url}/deliveries",
                json=delivery_payload,
                timeout=timeout,
            )
            if resp.status_code == 201:
                created_deliveries += 1
            elif resp.status_code == 200:
                skipped_duplicates += 1
            else:
                raise RuntimeError(
                    f"Failed to create delivery via POST /deliveries: "
                    f"status={resp.status_code}, body={resp.text}"
                )

    return {
        "fetched_alerts": len(alerts),
        "active_webhooks": len(active_webhooks),
        "created_deliveries": created_deliveries,
        "skipped_duplicates": skipped_duplicates,
    }
