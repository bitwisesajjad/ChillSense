from datetime import datetime
from .extensions import db

class Shipment(db.Model):
    __tablename__ = 'shipments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    origin = db.Column(db.String(50), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    min_temperature = db.Column(db.Float, default=-25.0) 
    max_temperature = db.Column(db.Float, default=-18.0)
    readings = db.relationship("Reading", back_populates="shipment")
    alerts = db.relationship("Alert", back_populates="shipment")
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'origin': self.origin,
            'destination': self.destination, # updated
            'status': self.status,
            'min_temperature': self.min_temperature, # updated
            'max_temperature': self.max_temperature, # updated
            'created_at': str(self.created_at)
        }

class Reading(db.Model):
    __tablename__ = 'readings'
    id = db.Column(db.Integer, primary_key=True)
    temp = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=True) 
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id', ondelete='SET NULL'), nullable=True)
    shipment = db.relationship("Shipment", back_populates="readings")
    ts = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'temp': self.temp,
            'humidity': self.humidity, # updated
            'shipment_id': self.shipment_id, # updated
            'ts': str(self.ts)
        }

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String(200))
    severity = db.Column(db.String(20), default='warning') 
    is_resolved = db.Column(db.Boolean, default=False)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False) # updated
    reading_id = db.Column(db.Integer, db.ForeignKey('readings.id', ondelete='SET NULL'), nullable=True) # updated
    shipment = db.relationship("Shipment", back_populates="alerts")
    reading = db.relationship("Reading") # updated
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'msg': self.msg,
            'severity': self.severity, # updated
            'is_resolved': self.is_resolved, # updated
            'shipment_id': self.shipment_id, # updated
            'reading_id': self.reading_id,
            'created_at': str(self.created_at) # updated
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50)) 
    details = db.Column(db.String(200))
    ts = db.Column(db.DateTime, default=datetime.now)