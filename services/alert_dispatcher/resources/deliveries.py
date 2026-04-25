"""Delivery resources for alert-dispatcher API."""

from flask import jsonify
from flask_restful import Resource

from ..models import Delivery


class DeliveriesListResource(Resource):
    """Resource for listing delivery attempts."""

    def get(self):
        """Return all deliveries ordered by newest first."""
        deliveries = Delivery.query.order_by(Delivery.created_at.desc(), Delivery.id.desc()).all()
        print(f"Fetched {len(deliveries)} deliveries")
        return jsonify([row.to_dict() for row in deliveries])
