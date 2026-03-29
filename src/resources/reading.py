"""Single reading resource for ChillSense API."""

from flask import abort, jsonify
from flask_restful import Resource

from ..models import Reading, Shipment


class ReadingResource(Resource):
    """Resource for retrieving and updating a single reading."""

    def get(self, reading: Reading, shipment: Shipment):
        """Return a single reading by id."""
        if reading.shipment_id != shipment.id:
            abort(404, description="Reading not found for this shipment")
        reading_data = reading.to_dict()
        reading_data["_links"] = {
            "self": f"/api/shipments/{shipment.id}/readings/{reading.id}",
            "shipment": f"/api/shipments/{shipment.id}"
        }
        return jsonify(reading_data)
