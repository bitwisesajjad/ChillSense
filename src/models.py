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
            'dest': self.destination,
            'status': self.status,
            'min_temp': self.min_temperature,
            'max_temp': self.max_temperature,
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
            'hum': self.humidity,
            'shp_id': self.shipment_id,
            'ts': str(self.ts)
        }

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String(200))
    severity = db.Column(db.String(20), default='warning') 
    is_resolved = db.Column(db.Boolean, default=False)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=False)
    reading_id = db.Column(db.Integer, db.ForeignKey('readings.id'), nullable=True)
    shipment = db.relationship("Shipment", back_populates="alerts")
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'msg': self.msg,
            'sev': self.severity,
            'resolved': self.is_resolved,
            'shp_id': self.shipment_id,
            'reading_id': self.reading_id,
            'ts': str(self.created_at)
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50)) 
    details = db.Column(db.String(200))
    ts = db.Column(db.DateTime, default=datetime.now)