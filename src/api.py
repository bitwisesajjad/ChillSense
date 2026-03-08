"""API routes for ChillSense."""

from flask import Blueprint, jsonify
from flask_restful import Api
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter
from .models import Shipment, Reading

from .resources.shipments import ShipmentsListResource
from .resources.shipment import ShipmentResource

from .resources.readings import ReadingsListResource
from .resources.reading import ReadingResource

from src.resources.alerts import AlertsListResource

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

class ShipmentConverter(BaseConverter):
    """Resolve shipment_id from URL to a Shipment ORM object."""

    def to_python(self, value):
        shipment = Shipment.query.filter_by(id=value).first()
        if shipment is None:
            raise NotFound
        return shipment

    def to_url(self, value):
        return str(value.id)


class ReadingConverter(BaseConverter):
    """Resolve reading_id from URL to a Reading ORM object."""

    def to_python(self, value):
        reading = Reading.query.filter_by(id=value).first()
        if reading is None:
            raise NotFound
        return reading

    def to_url(self, value):
        return str(value.id)


@api_bp.app_errorhandler(404)
def api_not_found(e):
    """Return JSON 404 for all /api routes."""
    return jsonify({"message": "Not Found"}), 404

api.add_resource(ShipmentsListResource, "/shipments")
# api.add_resource(ShipmentResource, "/shipments/<int:shipment_id>")
api.add_resource(ShipmentResource, "/shipments/<shipment:shipment>")

# api.add_resource(ReadingsListResource, "/readings")
api.add_resource(ReadingsListResource, "/shipments/<shipment:shipment>/readings")
# # api.add_resource(ReadingResource, "/readings/<int:reading_id>")
# api.add_resource(ReadingResource, "/readings/<reading:reading>")
api.add_resource(ReadingResource, "/shipments/<shipment:shipment>/readings/<reading:reading>")

api.add_resource(AlertsListResource, "/shipments/<shipment:shipment>/alerts")
