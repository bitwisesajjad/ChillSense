"""Webhook resources for alert-dispatcher API."""

from flask import jsonify
from flask_restful import Resource

from ..models import Webhook


class WebhooksListResource(Resource):
    """Resource for listing webhook configurations."""

    def get(self):
        """Return all webhooks ordered by id."""
        webhooks = Webhook.query.order_by(Webhook.id.asc()).all()
        return jsonify([w.to_dict() for w in webhooks])
