"""ChillSense API client used by the alert-dispatcher poller."""

import os

import requests
from requests import RequestException


def fetch_active_alerts():
    """Fetch alerts and return unresolved entries in normalized form."""
    base_url = os.getenv("CHILLSENSE_BASE_URL", "").strip()
    raw_timeout = os.getenv("REQUEST_TIMEOUT_SECONDS", "5")
    timeout = float(raw_timeout)

    base_url = base_url.rstrip("/")
    alerts_url = f"{base_url}/api/alerts"

    try:
        response = requests.get(alerts_url, timeout=timeout)
        response.raise_for_status()
    except RequestException as exc:
        raise RuntimeError(f"Failed to fetch alerts from {alerts_url}") from exc

    alerts = response.json()
    normalized_alerts = []

    for alert in alerts:
        if alert.get("is_resolved") is False:
            normalized_alerts.append(
                {
                    "alert_id": alert.get("id"),
                    "shipment_id": alert.get("shipment_id"),
                    "reading_id": alert.get("reading_id"),
                    "severity": alert.get("severity"),
                    "message": alert.get("msg"),
                    "created_at": alert.get("created_at"),
                }
            )

    return normalized_alerts
