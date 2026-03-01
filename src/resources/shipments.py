"""Shipment resources for ChillSense API."""

from flask import abort, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from jsonschema import ValidationError, validate

from ..extensions import db, cache
from ..models import Shipment


def page_key(*_args, **_kwargs):
    """Cache key for shipments page endpoint"""
    page = request.args.get("page", 0)
    return request.path + f"[page_{page}]"


class ShipmentsListResource(Resource):
    """Resource for listing all shipments and creating a new shipment."""

    def _clear_cache(self):
        """Clear cached shipment collection responses"""
        collection_path = request.path
        cache.delete_many((
            collection_path,
            request.path,
        ))

    @cache.cached(timeout=None, make_cache_key=page_key)
    def get(self):
        """Return all shipments."""
        shipments = Shipment.query.order_by(Shipment.id.asc()).all()
        return jsonify([s.to_dict() for s in shipments])

    def post(self):
        """Create a new shipment."""
        if request.json is None:
            abort(415, description="Request must contain a valid JSON body")

        try:
            validate(request.json, Shipment.json_schema())

            shipment = Shipment()
            shipment.deserialize(request.json)
            db.session.add(shipment)
            db.session.commit()
        except ValidationError as e:
            abort(400, description=str(e))
        except ValueError:
            db.session.rollback()
            abort(400, description="Invalid shipment update data")
        except IntegrityError:
            db.session.rollback()
            abort(409, description="Database integrity constraint violated")

        self._clear_cache()

        resp = jsonify(shipment.to_dict())
        resp.status_code = 201
        resp.headers["Location"] = f"/api/shipments/{shipment.id}"
        return resp
