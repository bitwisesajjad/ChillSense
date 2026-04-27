"""Alerts resources for ChillSense API."""

from flask import jsonify
from flask_restful import Resource

from ..models import Alert, Shipment


class AlertsGlobalListResource(Resource):
    """Resource for listing alerts across all shipments."""

    def get(self):
        """Return all alerts ordered by created_at, shipment_id, id."""
        alerts = (
            Alert.query
            .order_by(Alert.created_at.asc(), Alert.shipment_id.asc(), Alert.id.asc())
            .all()
        )
        return jsonify([r.to_dict() for r in alerts])


class AlertsListResource(Resource):
    """Resource for listing and creating alerts."""

    def get(self, shipment: Shipment):
        """Return all alerts for a shipment and order them by id."""
        alerts = Alert.query.filter_by(shipment_id=shipment.id).order_by(Alert.id.asc()).all()
        return jsonify([r.to_dict() for r in alerts])
