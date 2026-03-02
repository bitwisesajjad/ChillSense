"""Single shipment resource for ChillSense API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from jsonschema import ValidationError, validate

from ..extensions import db, cache
from ..models import Shipment, require_admin

class ShipmentResource(Resource):
    """Resource for reading, updating and deleting a single shipment."""

    def _clear_cache(self):
        """Clear cached shipment item and collection responses."""
        collection_path = "/api/shipments"
        cache.delete_many(
            collection_path,
            request.path,
        )

    def get(self, shipment: Shipment):
        """Return one shipment."""
        return jsonify(shipment.to_dict())

    def put(self, shipment: Shipment):
        """Replace shipment fields."""
        if request.json is None:
            abort(415, description="Request must contain a valid JSON body")

        try:
            validate(request.json, Shipment.json_schema())

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
            abort(409, description="Database integrity violated")

        return jsonify(shipment.to_dict())

    @require_admin
    def delete(self, shipment: Shipment):
        """Delete a shipment."""
        db.session.delete(shipment)
        db.session.commit()
        self._clear_cache()
        return "", 204
