from flask import Flask
from src.extensions import db
from src.models import Shipment, Reading, Alert, AuditLog

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://user:password@localhost:5432/coldchain"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    # db.drop_all()
    db.create_all()

    # Seed Shipments
    s1 = Shipment(
        id=1,
        name="Truck-001 (Pfizer)",
        origin="Berlin",
        destination="Munich",
        status="active",
        min_temperature=2.0,
        max_temperature=8.0,
    )
    s2 = Shipment(
        id=2,
        name="Truck-101 (Maersk-Meat)",
        origin="Oslo",
        destination="Hamburg",
        status="active",
        min_temperature=-25.0,
        max_temperature=-18.0,
    )
    s3 = Shipment(
        id=3,
        name="Truck-201 (Chiquita)",
        origin="Quito",
        destination="Rotterdam",
        status="active",
        min_temperature=12.0,
        max_temperature=14.0,
    )
    db.session.add_all([s1, s2, s3])
    db.session.commit()

    # Seed Readings
    r1 = Reading(id=1, temp=5.5, humidity=65.0, shipment_id=1)
    r2 = Reading(id=2, temp=-20.5, humidity=80.0, shipment_id=2)
    r3 = Reading(id=3, temp=13.0, humidity=90.0, shipment_id=3)
    db.session.add_all([r1, r2, r3])
    db.session.commit()

    # Seed Alerts
    a1 = Alert(
        id=1,
        msg="Temperature above threshold for vaccine cargo",
        severity="critical",
        is_resolved=False,
        shipment_id=1,
        reading_id=1,
    )
    a2 = Alert(
        id=2,
        msg="Temperature below threshold for meat cargo",
        severity="warning",
        is_resolved=True,
        shipment_id=2,
        reading_id=2,
    )
    db.session.add_all([a1, a2])
    db.session.commit()

    # Seed AuditLogs
    log1 = AuditLog(
        id=1, action="CREATE_SHIPMENT", details="Seed shipment Truck-001 (Pfizer)"
    )
    log2 = AuditLog(
        id=2, action="CREATE_READING", details="Initial reading for Truck-001 (Pfizer)"
    )
    db.session.add_all([log1, log2])
    db.session.commit()

print("Database initialized with hardcoded seed data!")

# docker exec -it postgres-db psql -U user -d coldchain
# \dt
# SELECT * FROM shipments;
# SELECT * FROM readings;
