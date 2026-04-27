"""API routes for alert-dispatcher service."""

from flask import Blueprint
from flask_restful import Api

from .resources.deliveries import DeliveriesListResource
from .resources.polling_now import PollingNowResource
from .resources.webhooks import WebhookResource, WebhooksListResource

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

api.add_resource(DeliveriesListResource, "/deliveries")
api.add_resource(WebhooksListResource, "/webhooks")
api.add_resource(WebhookResource, "/webhooks/<int:webhook_id>")
api.add_resource(PollingNowResource, "/polling-now")
