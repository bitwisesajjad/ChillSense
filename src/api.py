"""API routes for ChillSense."""

from flask import Blueprint, abort, jsonify, request
from flask_restful import Api
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Shipment, Reading
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from .resources.shipments import ShipmentsListResource
from .resources.shipment import ShipmentResource

from .resources.readings import ReadingsListResource
from .resources.reading import ReadingResource

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

class ShipmentConverter(BaseConverter):
    """Resolve shipment_id from URL to a Shipment ORM object."""

    def to_python(self, shipment_id):
        shipment = Shipment.query.filter_by(id=shipment_id).first()
        if shipment is None:
            raise NotFound
        return shipment

    def to_url(self, shipment):
        return str(shipment.id)


class ReadingConverter(BaseConverter):
    """Resolve reading_id from URL to a Reading ORM object."""

    def to_python(self, reading_id):
        reading = Reading.query.filter_by(id=reading_id).first()
        if reading is None:
            raise NotFound
        return reading

    def to_url(self, reading):
        return str(reading.id)


@api_bp.app_errorhandler(404)
def api_not_found(err):
    """Return JSON 404 for all /api routes."""
    return jsonify({"message": "Not Found"}), 404

api.add_resource(ShipmentsListResource, "/shipments")
# api.add_resource(ShipmentResource, "/shipments/<int:shipment_id>")
api.add_resource(ShipmentResource, "/shipments/<shipment:shipment>")

api.add_resource(ReadingsListResource, "/readings")
# api.add_resource(ReadingResource, "/readings/<int:reading_id>")
api.add_resource(ReadingResource, "/readings/<reading:reading>")
