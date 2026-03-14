"""Single alert resource for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from jsonschema import ValidationError, validate

from ..extensions import db
from ..models import Alert, Shipment


class AlertResource(Resource):
    """Resource for retrieving and updating a single alert."""

    def get(self, alert: Alert, shipment: Shipment):
        """Return a single alert by id."""
        if alert.shipment_id != shipment.id:
            abort(404, description="Alert not found for this shipment")
        return jsonify(alert.to_dict())

    def put(self, alert: Alert, shipment: Shipment):
        """Update an existing alert."""
        if request.json is None:
            abort(415, description="Request must contain a valid JSON body")

        payload = dict(request.json)
        payload["shipment_id"] = shipment.id

        try:
            validate(payload, Alert.json_schema())
            alert.deserialize(payload)
        except ValidationError as e:
            abort(400, description=str(e))
        except (TypeError, ValueError):
            abort(400, description="Invalid alert update data")

        if alert.shipment_id != shipment.id:
            abort(400, description="Alert does not belong to this shipment")

        db.session.add(alert)
        db.session.commit()
        return jsonify(alert.to_dict())
