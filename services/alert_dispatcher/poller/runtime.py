"""Continuous polling loop for alert-dispatcher."""

import os
import time

from .. import create_app
from ..extensions import db
from .dispatcher import poll_and_dispatch_alerts


def _read_poll_interval_seconds():
    """Read and validate polling interval from environment."""
    raw_value = os.getenv("POLL_INTERVAL_SECONDS", "15").strip()
    try:
        interval = float(raw_value)
    except ValueError as exc:
        raise ValueError("POLL_INTERVAL_SECONDS must be a number") from exc

    if interval <= 0:
        raise ValueError("POLL_INTERVAL_SECONDS must be greater than 0")

    return interval


def run_polling_loop(sleep_fn=time.sleep, max_cycles=None):
    """Run dispatch polling loop with a fixed sleep interval."""
    if max_cycles is not None and max_cycles <= 0:
        raise ValueError("max_cycles must be greater than 0")

    interval = _read_poll_interval_seconds()
    app = create_app()
    cycle = 0

    while True:
        cycle += 1
        with app.app_context():
            try:
                summary = poll_and_dispatch_alerts()
                print(f"[alert-dispatcher-poller] cycle={cycle} summary={summary}")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                # Keep poller alive and clean failed transaction state.
                db.session.rollback()
                print(f"[alert-dispatcher-poller] cycle={cycle} error={exc}")

        if max_cycles is not None and cycle >= max_cycles:
            break

        sleep_fn(interval)


def main():
    """CLI entrypoint for module execution."""
    run_polling_loop()
