import secrets

from flask import Flask
from src.extensions import db
from src.models import Shipment, Reading, Alert, AuditLog, ApiKey

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://user:password@localhost:5432/coldchain"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

    # Seed Shipments
    s1 = Shipment(
        name="Truck-001 (Pfizer)",
        origin="Berlin",
        destination="Munich",
        status="active",
        min_temperature=2.0,
        max_temperature=8.0,
    )
    s2 = Shipment(
        name="Truck-101 (Maersk-Meat)",
        origin="Oslo",
        destination="Hamburg",
        status="active",
        min_temperature=-25.0,
        max_temperature=-18.0,
    )
    s3 = Shipment(
        name="Truck-201 (Chiquita)",
        origin="Quito",
        destination="Rotterdam",
        status="active",
        min_temperature=12.0,
        max_temperature=14.0,
    )
    db.session.add_all([s1, s2, s3])

    # Seed Readings
    r1 = Reading(temp=5.5, humidity=65.0, shipment=s1)
    r2 = Reading(temp=-20.5, humidity=80.0, shipment=s2)
    r3 = Reading(temp=13.0, humidity=90.0, shipment=s3)
    db.session.add_all([r1, r2, r3])

    # Seed Alerts
    a1 = Alert(
        msg="Temperature above threshold for vaccine cargo",
        severity="critical",
        is_resolved=False,
        shipment=s1,
        reading=r1,
    )
    a2 = Alert(
        msg="Temperature below threshold for meat cargo",
        severity="warning",
        is_resolved=True,
        shipment=s2,
        reading=r2
    )
    db.session.add_all([a1, a2])

    # Seed AuditLogs
    log1 = AuditLog(
        action="CREATE_SHIPMENT", details="Seed shipment Truck-001 (Pfizer)"
    )
    log2 = AuditLog(
        action="CREATE_READING", details="Initial reading for Truck-001 (Pfizer)"
    )
    db.session.add_all([log1, log2])

    # Seed API Key
    token = secrets.token_urlsafe()
    db_key = ApiKey(
        key=ApiKey.key_hash(token),
        admin=True
    )
    db.session.add(db_key)

    db.session.commit()
    print(token)

print("Database initialized with seed data!")

# docker exec -it postgres-db psql -U user -d coldchain
# \dt
# SELECT * FROM shipments;
# SELECT * FROM readings;
