"""Readings resources for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource

from ..extensions import db
from ..models import Reading, Shipment


class ReadingsListResource(Resource):
    """Resource for listing and creating readings."""

    def get(self):
        """Return all readings and order them by id."""
        readings = Reading.query.order_by(Reading.id.asc()).all()
        return jsonify([r.to_dict() for r in readings])

    def post(self):
        """Create a new reading."""
        payload = request.get_json(silent=True) or {}

        if "temp" not in payload:
            abort(400)

        try:
            temp = float(payload["temp"])
        except (TypeError, ValueError):
            abort(400)

        humidity = payload.get("humidity")
        if humidity is not None:
            try:
                humidity = float(humidity)
            except (TypeError, ValueError):
                abort(400)

        shipment_id = payload.get("shipment_id")
        if shipment_id is not None:
            try:
                shipment_id = int(shipment_id)
            except (TypeError, ValueError):
                abort(400)

            shipment = Shipment.query.get(shipment_id)
            if shipment is None:
                abort(404)

        reading = Reading(
            temp=temp,
            humidity=humidity,
            shipment_id=shipment_id,
        )
        db.session.add(reading)
        db.session.commit()

        resp = jsonify(reading.to_dict())
        resp.status_code = 201
        resp.headers["Location"] = f"/api/readings/{reading.id}"
        return resp