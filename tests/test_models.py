from src.models import Alert, ApiKey, AuditLog, Reading, Shipment


def test_shipment_repr_returns_string():
    """Shipment.__repr__ returns a readable string."""
    shipment = Shipment()
    shipment.id = 1
    shipment.name = "S1"
    assert "<Shipment id=1 name='S1'>" == repr(shipment)


def test_reading_repr_returns_string():
    """Reading.__repr__ returns a readable string."""
    reading = Reading()
    reading.id = 2
    reading.shipment_id = 1
    reading.temp = -5
    assert "<Reading id=2 shipment_id=1 temp=-5>" == repr(reading)


def test_alert_to_dict_contains_expected_fields():
    """Alert.to_dict returns expected alert fields."""
    alert = Alert()
    alert.id = 1
    alert.msg = "Too cold"
    alert.severity = "warning"
    alert.is_resolved = False
    alert.shipment_id = 2
    alert.reading_id = 3
    alert.created_at = None

    data = alert.to_dict()

    assert data["id"] == 1
    assert data["msg"] == "Too cold"
    assert data["severity"] == "warning"
    assert data["is_resolved"] is False
    assert data["shipment_id"] == 2
    assert data["reading_id"] == 3


def test_alert_repr_returns_string():
    """Alert.__repr__ returns a readable string."""
    alert = Alert()
    alert.id = 1
    alert.shipment_id = 2
    alert.severity = "warning"
    assert "<Alert id=1 shipment_id=2 severity='warning'>" == repr(alert)


def test_auditlog_to_dict_contains_expected_fields():
    """AuditLog.to_dict returns expected audit log fields."""
    log = AuditLog()
    log.id = 1
    log.action = "delete"
    log.details = "Shipment removed"
    log.ts = None

    data = log.to_dict()

    assert data["id"] == 1
    assert data["action"] == "delete"
    assert data["details"] == "Shipment removed"


def test_auditlog_repr_returns_string():
    """AuditLog.__repr__ returns a readable string."""
    log = AuditLog()
    log.id = 1
    log.action = "delete"
    assert "<AuditLog id=1 action='delete'>" == repr(log)


def test_apikey_repr_returns_string():
    """ApiKey.__repr__ returns a readable string."""
    key = ApiKey()
    key.id = 1
    key.shipment_id = 2
    key.admin = True
    assert "<ApiKey id=1 shipment_id=2 admin=True>" == repr(key)