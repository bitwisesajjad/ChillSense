"""Delivery resources for alert-dispatcher API."""

from flask import abort, jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Delivery


class DeliveriesListResource(Resource):
    """Resource for listing and creating delivery attempts."""

    def get(self):
        """Return all deliveries ordered by newest first."""
        deliveries = Delivery.query.order_by(Delivery.created_at.desc(), Delivery.id.desc()).all()
        print(f"Fetched {len(deliveries)} deliveries")
        return jsonify([row.to_dict() for row in deliveries])

    def post(self):
        """Create a delivery attempt row."""
        payload = request.get_json(silent=True)
        if payload is None:
            abort(415, description="Request must contain a valid JSON body")
        payload = dict(payload)

        allowed_fields = {
            "alert_id",
            "shipment_id",
            "webhook_id",
            "target_url",
            "status",
            "response_code",
            "error_message",
            "attempt_count",
        }
        required_fields = {"alert_id", "webhook_id", "target_url", "status"}
        if set(payload.keys()) - allowed_fields:
            abort(400, description="Request contains unsupported fields")
        if not required_fields.issubset(payload):
            abort(400, description="Missing required delivery fields")

        if not isinstance(payload["alert_id"], int) or payload["alert_id"] <= 0:
            abort(400, description="alert_id must be a positive integer")
        if payload.get("shipment_id") is not None and not isinstance(payload["shipment_id"], int):
            abort(400, description="shipment_id must be an integer or null")
        if not isinstance(payload["webhook_id"], int) or payload["webhook_id"] <= 0:
            abort(400, description="webhook_id must be a positive integer")
        if not isinstance(payload["target_url"], str) or not payload["target_url"].strip():
            abort(400, description="target_url must be a non-empty string")
        if payload["status"] not in {"sent", "failed"}:
            abort(400, description="status must be either 'sent' or 'failed'")
        if payload.get("response_code") is not None and not isinstance(payload["response_code"], int):
            abort(400, description="response_code must be an integer or null")
        if payload.get("error_message") is not None and not isinstance(payload["error_message"], str):
            abort(400, description="error_message must be a string or null")
        if not isinstance(payload.get("attempt_count", 1), int) or payload.get("attempt_count", 1) <= 0:
            abort(400, description="attempt_count must be a positive integer")

        delivery = Delivery(
            alert_id=payload["alert_id"],
            shipment_id=payload.get("shipment_id"),
            webhook_id=payload["webhook_id"],
            target_url=payload["target_url"],
            status=payload["status"],
            response_code=payload.get("response_code"),
            error_message=payload.get("error_message"),
            attempt_count=payload.get("attempt_count", 1),
        )
        db.session.add(delivery)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            duplicate = Delivery.query.filter_by(
                alert_id=payload.get("alert_id"),
                shipment_id=payload.get("shipment_id"),
                webhook_id=payload.get("webhook_id"),
            ).first()
            if duplicate is not None:
                return jsonify(duplicate.to_dict())
            abort(400, description="Invalid delivery payload")

        resp = jsonify(delivery.to_dict())
        resp.status_code = 201
        resp.headers["Location"] = f"/deliveries/{delivery.id}"
        return resp
