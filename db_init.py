import secrets
import time
from sqlalchemy.exc import OperationalError
from src import create_app
from src.extensions import db
from src.models import Shipment, Reading, Alert, AuditLog, ApiKey


def init_db_once():
    app = create_app()

    with app.app_context():
        db.create_all()

        # Only seed if there are no shipments yet
        if Shipment.query.first() is None:
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
                reading=r2,
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

        # Create an admin API key only if none exists
        existing = ApiKey.query.filter_by(admin=True).first()
        if existing is None:
            token = secrets.token_urlsafe()
            db_key = ApiKey(
                key=ApiKey.key_hash(token),
                admin=True,
            )
            db.session.add(db_key)
            db.session.commit()
            print(f"Generated admin API token: {token}")
        else:
            print("Admin API key already exists (not printing token).")

        print("Database initialized with seed data!")


if __name__ == "__main__":
    # A simple retry loop so running inside containers waits briefly for DB readiness
    attempts = 0
    while attempts < 10:
        try:
            init_db_once()
            break
        except OperationalError as exc:
            attempts += 1
            print(f"db_init attempt {attempts} failed: {exc}")
            time.sleep(2)
    else:
        print("db_init failed after retries")

# docker exec -it postgres-db psql -U user -d coldchain
# \dt
# SELECT * FROM shipments;
# SELECT * FROM readings;
