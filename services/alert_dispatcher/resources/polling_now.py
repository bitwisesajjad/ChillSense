"""Polling trigger resource for alert-dispatcher API."""

from flask import abort, jsonify
from flask_restful import Resource

from ..extensions import db
from ..poller.dispatcher import poll_and_dispatch_alerts


class PollingNowResource(Resource):
    """Demo-only resource for triggering one immediate poll-and-dispatch cycle."""

    def get(self):
        """Run poll-and-dispatch exactly once for demo/manual troubleshooting."""
        try:
            summary = poll_and_dispatch_alerts()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            db.session.rollback()
            abort(502, description=f"Polling failed: {exc}")

        return jsonify(
            {
                "message": "Demo polling executed once",
                "summary": summary,
            }
        )
