"""API routes for alert-dispatcher service."""

from flask import Blueprint
from flask_restful import Api

from .resources.webhooks import WebhooksListResource

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

api.add_resource(WebhooksListResource, "/webhooks")
