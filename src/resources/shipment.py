"""Single shipment resource for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Shipment, require_admin

class ShipmentResource(Resource):
    """Resource for reading, updating and deleting a single shipment."""

    def get(self, shipment_id: int):
        """Return one shipment."""
        shipment = Shipment.query.get(shipment_id)
        if shipment is None:
            abort(404)
        return jsonify(shipment.to_dict())

    def put(self, shipment_id: int):
        """Replace shipment fields."""
        if request.json is None:
            abort(415)

        shipment = Shipment.query.get(shipment_id)
        if shipment is None:
            abort(404)

        try:
            shipment.name = request.json["name"]
            shipment.origin = request.json["origin"]
            shipment.destination = request.json["destination"]
            shipment.status = request.json.get("status", shipment.status)
            shipment.min_temperature = float(request.json["min_temperature"])
            shipment.max_temperature = float(request.json["max_temperature"])
            db.session.commit()
        except (KeyError, ValueError):
            db.session.rollback()
            abort(400)
        except IntegrityError:
            db.session.rollback()
            abort(409)

        return jsonify(shipment.to_dict())

    @require_admin
    def delete(self, shipment_id: int):
        """Delete a shipment."""
        shipment = Shipment.query.get(shipment_id)
        if shipment is None:
            abort(404)

        db.session.delete(shipment)
        db.session.commit()
        return "", 204
