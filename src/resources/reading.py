"""Single reading resource for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from jsonschema import ValidationError, validate

from ..extensions import db
from ..models import Reading, Shipment


class ReadingResource(Resource):
    """Resource for retrieving and updating a single reading."""

    def get(self, reading: Reading):
        """Return a single reading by id."""
        return jsonify(reading.to_dict())

    def put(self, reading: Reading):
        """Update an existing reading."""
        if request.json is None:
            abort(415)

        try:
            validate(request.json, Reading.json_schema())
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
        return jsonify(reading.to_dict())
