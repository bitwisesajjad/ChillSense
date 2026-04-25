"""Tests for ChillSense client in alert-dispatcher service."""

from unittest.mock import Mock, patch

import pytest
import requests

from services.alert_dispatcher.clients import fetch_active_alerts


def test_fetch_active_alerts_returns_only_unresolved_alerts(monkeypatch):
    """fetch_active_alerts returns unresolved alerts in normalized shape."""
    monkeypatch.setenv("CHILLSENSE_BASE_URL", "http://localhost:5000")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "3")

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {
            "created_at": "2026-04-05 16:33:42.338279",
            "id": 1,
            "is_resolved": False,
            "msg": "Temperature above threshold for vaccine cargo",
            "reading_id": 1,
            "severity": "critical",
            "shipment_id": 1,
        },
        {
            "created_at": "2026-04-05 16:33:42.338284",
            "id": 2,
            "is_resolved": True,
            "msg": "Temperature below threshold for meat cargo",
            "reading_id": 2,
            "severity": "warning",
            "shipment_id": None,
        },
    ]

    with patch("services.alert_dispatcher.clients.requests.get", return_value=response) as mock_get:
        alerts = fetch_active_alerts()

    mock_get.assert_called_once_with("http://localhost:5000/api/alerts", timeout=3.0)
    assert alerts == [
        {
            "alert_id": 1,
            "shipment_id": 1,
            "reading_id": 1,
            "severity": "critical",
            "message": "Temperature above threshold for vaccine cargo",
            "created_at": "2026-04-05 16:33:42.338279",
        }
    ]


def test_fetch_active_alerts_filters_out_resolved_alerts(monkeypatch):
    """fetch_active_alerts excludes resolved alerts from the response."""
    monkeypatch.setenv("CHILLSENSE_BASE_URL", "http://localhost:5000")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "5")

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {
            "created_at": "2026-04-05 16:33:42.338284",
            "id": 2,
            "is_resolved": True,
            "msg": "Temperature below threshold for meat cargo",
            "reading_id": 2,
            "severity": "warning",
            "shipment_id": None,
        }
    ]

    with patch("services.alert_dispatcher.clients.requests.get", return_value=response):
        alerts = fetch_active_alerts()

    assert alerts == []


def test_fetch_active_alerts_handles_request_failure_predictably(monkeypatch):
    """fetch_active_alerts wraps request failures with a clear runtime error."""
    monkeypatch.setenv("CHILLSENSE_BASE_URL", "http://localhost:5000")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "5")

    with patch(
        "services.alert_dispatcher.clients.requests.get",
        side_effect=requests.RequestException("network down"),
    ):
        with pytest.raises(RuntimeError, match="Failed to fetch alerts"):
            fetch_active_alerts()
