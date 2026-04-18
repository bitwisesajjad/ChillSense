"""SQLAlchemy models for the alert-dispatcher service."""

from datetime import datetime

# from sqlalchemy import event, inspect

from .extensions import db


class Webhook(db.Model):
    """Webhook destination configuration."""

    __tablename__ = "Webhook"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    deliveries = db.relationship("Delivery", back_populates="webhook")

    __table_args__ = (
        db.CheckConstraint("status IN (0, 1)", name="ck_webhook_status"),
    )

    def set_status(self, new_status):
        """Only status is expected to change for webhook rows."""
        self.status = new_status


class Delivery(db.Model):
    """Delivery attempt for one alert to one webhook."""

    __tablename__ = "Delivery"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, nullable=False)
    webhook_id = db.Column(
        db.Integer,
        db.ForeignKey("Webhook.id", ondelete="RESTRICT"),
        nullable=False
    )
    target_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    response_code = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.String(255), nullable=True)
    attempt_count = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    webhook = db.relationship("Webhook", back_populates="deliveries")

    __table_args__ = (
        db.UniqueConstraint("alert_id", "webhook_id", name="uq_delivery_alert_webhook"),
        db.CheckConstraint("status IN ('sent', 'failed')", name="ck_delivery_status"),
    )


# def _raise_delete_blocked(_mapper, _connection, target):
#     """Block delete operations for immutable audit-style tables."""
#     raise ValueError(f"Delete is not allowed for {target.__tablename__}")


# def _enforce_webhook_update(_mapper, _connection, target):
#     """Allow webhook updates only for status (updated_at is auto-managed)."""
#     state = inspect(target)
#     changed_columns = {
#         attr.key
#         for attr in state.attrs
#         if attr.history.has_changes()
#     }
#     allowed_columns = {"status", "updated_at"}
#     if not changed_columns.issubset(allowed_columns):
#         raise ValueError("Webhook updates can only change status")


# def _raise_delivery_update_blocked(_mapper, _connection, _target):
#     """Block updates for delivery rows after insert."""
#     raise ValueError("Delivery rows are insert-only")


# event.listen(Webhook, "before_delete", _raise_delete_blocked)
# event.listen(Webhook, "before_update", _enforce_webhook_update)
# event.listen(Delivery, "before_delete", _raise_delete_blocked)
# event.listen(Delivery, "before_update", _raise_delivery_update_blocked)
