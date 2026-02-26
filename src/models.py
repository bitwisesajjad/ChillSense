"""SQLAlchemy ORM models for the ChillSense API."""
from datetime import datetime
import hashlib
from src.extensions import db


class Shipment(db.Model):
    """Represents a shipment tracked by the system."""
    __tablename__ = "shipments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    origin = db.Column(db.String(50), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="active")
    min_temperature = db.Column(db.Float, default=-25.0)
    max_temperature = db.Column(db.Float, default=-18.0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    readings = db.relationship("Reading", back_populates="shipment")
    alerts = db.relationship("Alert", back_populates="shipment")

    api_key = db.relationship("ApiKey", back_populates="shipment")

    def to_dict(self):
        """Serialize the shipment to a JSON-friendly dict."""
        return {
            "id": self.id,
            "name": self.name,
            "origin": self.origin,
            "destination": self.destination,
            "status": self.status,
            "min_temperature": self.min_temperature,
            "max_temperature": self.max_temperature,
            "created_at": str(self.created_at),
        }

    # for PyLint “too few public methods”
    def __repr__(self):
        """Return a string representation."""
        return f"<Shipment id={self.id} name={self.name!r}>"


class Reading(db.Model):
    """Single sensor reading (temperature/humidity) for a shipment."""
    __tablename__ = "readings"
    id = db.Column(db.Integer, primary_key=True)
    temp = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=True)
    shipment_id = db.Column(
        db.Integer, db.ForeignKey("shipments.id", ondelete="SET NULL"),
        nullable=True
    )
    alert = db.relationship("Alert", back_populates="reading", uselist=False)
    ts = db.Column(db.DateTime, default=datetime.now)

    shipment = db.relationship("Shipment", back_populates="readings")

    def to_dict(self):
        """Serialize the reading to a JSON-friendly dict."""
        return {
            "id": self.id,
            "temp": self.temp,
            "humidity": self.humidity,
            "shipment_id": self.shipment_id,
            "ts": str(self.ts),
        }

    def __repr__(self):
        """Return a string representation."""
        return f"<Reading id={self.id} shipment_id={self.shipment_id} temp={self.temp}>"


class Alert(db.Model):
    """Alert created when readings violate shipment thresholds."""
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String(200))
    severity = db.Column(db.String(20), default="warning")
    is_resolved = db.Column(db.Boolean, default=False)
    shipment_id = db.Column(
        db.Integer, db.ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True
    )
    reading_id = db.Column(
        db.Integer, db.ForeignKey("readings.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.now)

    shipment = db.relationship("Shipment", back_populates="alerts")
    reading = db.relationship("Reading", back_populates="alert")

    def to_dict(self):
        """Serialize the alert to a JSON-friendly dict."""
        return {
            "id": self.id,
            "msg": self.msg,
            "severity": self.severity,
            "is_resolved": self.is_resolved,
            "shipment_id": self.shipment_id,
            "reading_id": self.reading_id,
            "created_at": str(self.created_at),
        }

    def __repr__(self):
        """Return a string representation."""
        return f"<Alert id={self.id} shipment_id={self.shipment_id} severity={self.severity!r}>"


class AuditLog(db.Model):
    """Audit log entry for an action performed in the system."""
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50))
    details = db.Column(db.String(200))
    ts = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        """Serialize the audit log entry to a JSON-friendly dict."""
        return {
            "id": self.id,
            "action": self.action,
            "details": self.details,
            "ts": str(self.ts),
        }

    def __repr__(self):
        """Return a string representation."""
        return f"<AuditLog id={self.id} action={self.action!r}>"


class ApiKey(db.Model):
    """API key linked to a shipment or admin access."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), nullable=False, unique=True)
    shipment_id = db.Column(
        db.Integer, db.ForeignKey("shipments.id",
        ondelete="SET NULL"),
        nullable=True,
        )
    admin =  db.Column(db.Boolean, default=False)

    shipment = db.relationship("Shipment", back_populates="api_key", uselist=False)

    @staticmethod
    def key_hash(key):
        """Return a SHA-256 hex digest for given key string."""
        return hashlib.sha256(key.encode()).hexdigest()
    def __repr__(self):
        """Return a string representation."""
        return f"<ApiKey id={self.id} shipment_id={self.shipment_id} admin={self.admin}>"
