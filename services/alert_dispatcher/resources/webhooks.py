"""Webhook resources for alert-dispatcher API."""

from flask import abort, jsonify, request
from flask_restful import Resource

from ..extensions import db

from ..models import Webhook


class WebhooksListResource(Resource):
    """Resource for listing webhook configurations."""

    def get(self):
        """Return all webhooks ordered by id."""
        webhooks = Webhook.query.order_by(Webhook.id.asc()).all()
        return jsonify([w.to_dict() for w in webhooks])


class WebhookResource(Resource):
    """Resource for updating a single webhook configuration."""

    def put(self, webhook_id):
        """Update webhook status by id."""
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or set(payload.keys()) != {"status"}:
            abort(400, description="Only 'status' is allowed in request body")

        status = payload.get("status")
        if status not in (0, 1):
            abort(400, description="Invalid status value. Allowed values are 0 or 1")

        webhook = db.session.get(Webhook, webhook_id)
        if webhook is None:
            abort(404, description="Webhook not found")

        if webhook.status != status:
            webhook.set_status(status)
            db.session.add(webhook)
            db.session.commit()

        return jsonify(webhook.to_dict())
