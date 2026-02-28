"""Single reading resource for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource

from ..extensions import db
from ..models import Reading, Shipment


class ReadingResource(Resource):
    """Resource for retrieving and updating a single reading."""

    def get(self, reading: Reading):
        """Return a single reading by id."""
        return jsonify(reading.to_dict())

    def put(self, reading: Reading):
        """Update an existing reading."""
        payload = request.get_json(silent=True) or {}

        if "temp" in payload:
            try:
                reading.temp = float(payload["temp"])
            except (TypeError, ValueError):
                abort(400)

        if "humidity" in payload:
            humidity = payload["humidity"]
            if humidity is None:
                reading.humidity = None
            else:
                try:
                    reading.humidity = float(humidity)
                except (TypeError, ValueError):
                    abort(400)

        if "shipment_id" in payload:
            shipment_id = payload["shipment_id"]

            if shipment_id is None:
                reading.shipment_id = None
            else:
                try:
                    shipment_id = int(shipment_id)
                except (TypeError, ValueError):
                    abort(400)

                shipment = Shipment.query.get(shipment_id)
                if shipment is None:
                    abort(404)

                reading.shipment_id = shipment_id

        db.session.commit()
        return jsonify(reading.to_dict())
