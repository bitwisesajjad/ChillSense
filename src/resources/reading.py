"""Single reading resource for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from jsonschema import ValidationError, validate

from ..extensions import db
from ..models import Reading, Shipment


class ReadingResource(Resource):
    """Resource for retrieving and updating a single reading."""

    def get(self, reading: Reading, shipment: Shipment):
        """Return a single reading by id."""
        if reading.shipment_id != shipment.id:
            abort(404, description="Reading not found for this shipment")
        return jsonify(reading.to_dict())

    # def put(self, reading: Reading, shipment: Shipment):
    #     """Update an existing reading."""
    #     if request.json is None:
    #         abort(415, description="Request must contain a valid JSON body")

    #     payload = dict(request.json)
    #     payload["shipment_id"] = shipment.id

    #     try:
    #         validate(payload, Reading.json_schema())
    #         reading.deserialize(payload)
    #     except ValidationError as e:
    #         abort(400, description=str(e))
    #     except (TypeError, ValueError):
    #         abort(400, description="Invalid reading update data")

    #     if reading.shipment_id != shipment.id:
    #         abort(400, description="Reading does not belong to this shipment")

    #     db.session.add(reading)
    #     db.session.commit()
    #     return jsonify(reading.to_dict())
