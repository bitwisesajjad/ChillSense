"""Alerts resources for ChillSense API."""

from flask import jsonify
from flask_restful import Resource

from ..models import Alert, Shipment


class AlertsListResource(Resource):
    """Resource for listing and creating alerts."""

    def get(self, shipment: Shipment):
        """Return all alerts and order them by id."""
        alerts = Alert.query.filter_by(shipment_id=shipment.id).order_by(Alert.id.asc()).all()
        return jsonify([r.to_dict() for r in alerts])
