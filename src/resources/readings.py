"""Readings resources for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from jsonschema import ValidationError, validate

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
        if request.json is None:
            abort(415)

        try:
            validate(request.json, Reading.json_schema())

            reading = Reading()
            reading.deserialize(request.json)
        except ValidationError as e:
            abort(400, description=str(e))
        except (TypeError, ValueError):
            abort(400)

        if reading.shipment_id is not None:
            shipment = Shipment.query.get(reading.shipment_id)
            if shipment is None:
                abort(404)

        db.session.add(reading)
        db.session.commit()

        resp = jsonify(reading.to_dict())
        resp.status_code = 201
        resp.headers["Location"] = f"/api/readings/{reading.id}"
        return resp
