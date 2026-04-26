"""Poller package for alert-dispatcher."""

from typing import TYPE_CHECKING

from .chillsense_client import fetch_active_alerts
from .dispatcher import poll_and_dispatch_alerts, send_webhook

if TYPE_CHECKING:
    # Imported only for static analysis and editor IntelliSense.
    from .runtime import main, run_polling_loop

__all__ = [
    "send_webhook",
    "fetch_active_alerts",
    "poll_and_dispatch_alerts",
    "run_polling_loop",
    "main",
]


def __getattr__(name):
    """Lazy-load runtime exports to avoid circular imports during app bootstrap."""
    if name in {"main", "run_polling_loop"}:
        from .runtime import main, run_polling_loop

        runtime_exports = {
            "main": main,
            "run_polling_loop": run_polling_loop,
        }
        return runtime_exports[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
