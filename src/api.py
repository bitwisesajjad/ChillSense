"""API routes for ChillSense."""

from flask import Blueprint, abort, jsonify, request
from flask_restful import Api
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Shipment, Reading

from .resources.shipments import ShipmentsListResource
from .resources.shipment import ShipmentResource

from .resources.readings import ReadingsListResource
from .resources.reading import ReadingResource

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

@api_bp.app_errorhandler(404)
def api_not_found(err):
    """Return JSON 404 for all /api routes."""
    return jsonify({"message": "Not Found"}), 404

api.add_resource(ShipmentsListResource, "/shipments")
api.add_resource(ShipmentResource, "/shipments/<int:shipment_id>")

api.add_resource(ReadingsListResource, "/readings")
api.add_resource(ReadingResource, "/readings/<int:reading_id>")
