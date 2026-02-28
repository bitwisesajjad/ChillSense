"""Shipment resources for ChillSense API."""

from flask import abort, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource

from ..extensions import db
from ..models import Shipment


class ShipmentsListResource(Resource):
    """Resource for listing all shipments and creating a new shipment."""

    def get(self):
        """Return all shipments."""
        shipments = Shipment.query.order_by(Shipment.id.asc()).all()
        return jsonify([s.to_dict() for s in shipments])

    def post(self):
        """Create a new shipment."""
        if request.json is None:
            abort(415)

        try:
            shipment = Shipment(
                name=request.json["name"],
                origin=request.json["origin"],
                destination=request.json["destination"],
                status=request.json.get("status", "active"),
                min_temperature=float(request.json.get("min_temperature", -25.0)),
                max_temperature=float(request.json.get("max_temperature", -18.0)),
            )
            db.session.add(shipment)
            db.session.commit()
        except (KeyError, ValueError):
            db.session.rollback()
            abort(400)
        except IntegrityError:
            db.session.rollback()
            abort(409)

        resp = jsonify(shipment.to_dict())
        resp.status_code = 201
        resp.headers["Location"] = f"/api/shipments/{shipment.id}"
        return resp