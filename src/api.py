"""API routes for ChillSense."""

from flask import Blueprint, abort, jsonify, request
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Shipment, Reading

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


@api_bp.get("/readings")
def readings_get():
    """Return all readings and order them by id."""
    readings = Reading.query.order_by(Reading.id.asc()).all()
    return jsonify([r.to_dict() for r in readings])

@api_bp.get("/readings/<int:reading_id>")
def readings_get_one(reading_id):
    """Return a single reading by id."""
    reading = Reading.query.get(reading_id)
    if reading is None:
        abort(404)
    return jsonify(reading.to_dict())


@api_bp.post("/readings")
def readings_post():
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

    return jsonify(reading.to_dict()), 201


@api_bp.put("/readings/<int:reading_id>")
def readings_put(reading_id):
    """Update an existing reading."""
    reading = Reading.query.get(reading_id)
    if reading is None:
        abort(404)

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
