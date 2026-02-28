"""API routes for ChillSense."""

from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Shipment

api_bp = Blueprint("api", __name__)

@api_bp.get("/shipments")
def shipments_get():
    """Return all shipments."""
    shipments = Shipment.query.order_by(Shipment.id.asc()).all()
    return jsonify([s.to_dict() for s in shipments])


@api_bp.post("/shipments")
def shipments_post():
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


@api_bp.get("/shipments/<int:shipment_id>")
def shipment_get(shipment_id):
    """Return one shipment."""
    shipment = Shipment.query.get(shipment_id)
    if shipment is None:
        abort(404)
    return jsonify(shipment.to_dict())


@api_bp.put("/shipments/<int:shipment_id>")
def shipment_put(shipment_id):
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


@api_bp.delete("/shipments/<int:shipment_id>")
def shipment_delete(shipment_id):
    """Delete a shipment."""
    shipment = Shipment.query.get(shipment_id)
    if shipment is None:
        abort(404)

    db.session.delete(shipment)
    db.session.commit()
    return "", 204
