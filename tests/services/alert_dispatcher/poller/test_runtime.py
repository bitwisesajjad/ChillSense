"""Tests for alert-dispatcher continuous poller runtime."""

from unittest.mock import patch

import pytest

from services.alert_dispatcher.poller.runtime import _read_poll_interval_seconds, run_polling_loop


def test_read_poll_interval_seconds_returns_float(monkeypatch):
    """POLL_INTERVAL_SECONDS is parsed as positive float."""
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "2.5")

    assert _read_poll_interval_seconds() == 2.5


@pytest.mark.parametrize("value", ["abc", "0", "-1"])
def test_read_poll_interval_seconds_rejects_invalid_values(monkeypatch, value):
    """Invalid poll interval values raise ValueError."""
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", value)

    with pytest.raises(ValueError):
        _read_poll_interval_seconds()


def test_run_polling_loop_runs_expected_cycles(monkeypatch):
    """run_polling_loop executes dispatch for each cycle and sleeps between cycles."""
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "1")

    with patch("services.alert_dispatcher.poller.runtime.create_app") as mock_create_app, patch(
        "services.alert_dispatcher.poller.runtime.poll_and_dispatch_alerts",
        return_value={"created_deliveries": 0},
    ) as mock_dispatch, patch(
        "services.alert_dispatcher.poller.runtime.db.session.rollback"
    ) as mock_rollback:
        app = mock_create_app.return_value
        app.app_context.return_value.__enter__.return_value = None
        app.app_context.return_value.__exit__.return_value = False

        sleep_calls = []

        def fake_sleep(seconds):
            sleep_calls.append(seconds)

        run_polling_loop(sleep_fn=fake_sleep, max_cycles=3)

    assert mock_dispatch.call_count == 3
    assert sleep_calls == [1.0, 1.0]
    mock_rollback.assert_not_called()


def test_run_polling_loop_rejects_invalid_max_cycles(monkeypatch):
    """max_cycles must be a positive integer when provided."""
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "1")

    with pytest.raises(ValueError, match="max_cycles"):
        run_polling_loop(max_cycles=0)


def test_run_polling_loop_rolls_back_on_dispatch_error(monkeypatch):
    """Dispatcher errors are handled and rollback is executed."""
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "1")

    with patch("services.alert_dispatcher.poller.runtime.create_app") as mock_create_app, patch(
        "services.alert_dispatcher.poller.runtime.poll_and_dispatch_alerts",
        side_effect=RuntimeError("boom"),
    ), patch("services.alert_dispatcher.poller.runtime.db.session.rollback") as mock_rollback:
        app = mock_create_app.return_value
        app.app_context.return_value.__enter__.return_value = None
        app.app_context.return_value.__exit__.return_value = False

        run_polling_loop(sleep_fn=lambda _seconds: None, max_cycles=1)

    mock_rollback.assert_called_once()


def test_main_calls_run_polling_loop():
    """main() delegates to run_polling_loop."""
    with patch("services.alert_dispatcher.poller.runtime.run_polling_loop") as mock_loop:
        from services.alert_dispatcher.poller.runtime import main

        main()

    mock_loop.assert_called_once_with()
