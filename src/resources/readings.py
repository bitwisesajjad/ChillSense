"""Readings resources for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from jsonschema import ValidationError, validate

from ..extensions import db
from ..models import Alert, Reading, Shipment


class ReadingsListResource(Resource):
    """Resource for listing and creating readings."""

    def get(self, shipment: Shipment):
        """Return all readings and order them by id."""
        readings = Reading.query.filter_by(shipment_id=shipment.id).order_by(Reading.id.asc()).all()
        return jsonify([r.to_dict() for r in readings])

    def post(self, shipment: Shipment):
        """Create a new reading."""
        if request.json is None:
            abort(415, description="Request must contain a valid JSON body")

        payload = dict(request.json)
        payload["shipment_id"] = shipment.id

        try:
            validate(payload, Reading.json_schema())

            reading = Reading()
            reading.deserialize(payload)
        except ValidationError as e:
            abort(400, description=str(e))
        except (TypeError, ValueError):
            abort(400, description="Invalid reading data or schema validation failed")

        db.session.add(reading)

        if reading.temp < shipment.min_temperature or reading.temp > shipment.max_temperature:
            alert = Alert(
                msg=(
                    f"Temperature {reading.temp}C is out of range [{shipment.min_temperature}, {shipment.max_temperature}]"
                ),
                shipment=shipment,
                reading=reading,
            )
            db.session.add(alert)

        db.session.commit()

        resp = jsonify([reading.to_dict(), alert.to_dict()])
        resp.status_code = 201
        resp.headers["Location"] = f"/api/shipments/{shipment.id}/readings/{reading.id}"
        return resp
