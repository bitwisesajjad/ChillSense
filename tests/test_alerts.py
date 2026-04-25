"""Tests for the Alerts API endpoints."""

from src.models import Alert


def create_shipment(client):
    """Create a shipment and return its JSON body."""
    resp = client.post(
        "/api/shipments",
        json={
            "name": "S1",
            "origin": "Oulu",
            "destination": "Helsinki",
            "min_temperature": -10,
            "max_temperature": 5,
        },
    )
    return resp.get_json()


def create_alert_via_reading(client, shipment_id, payload=None):
    """Create an alert indirectly via POST reading and return alert dict."""
    if payload is None:
        payload = {"temp": 10, "humidity": 30}

    resp = client.post(f"/api/shipments/{shipment_id}/readings", json=payload)
    data = resp.get_json()

    if isinstance(data, list):
        return data[1]

    return data


def test_alerts_get_list(client):
    """GET alerts list returns alerts for a shipment."""
    shipment = create_shipment(client)
    create_alert_via_reading(client, shipment["id"])

    resp = client.get(f"/api/shipments/{shipment['id']}/alerts")

    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_alerts_get_global_list(client):
    """GET /alerts returns alerts across all shipments."""
    s1 = create_shipment(client)
    s2 = create_shipment(client)
    a1 = create_alert_via_reading(client, s1["id"])
    a2 = create_alert_via_reading(client, s2["id"])

    resp = client.get("/api/alerts")

    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    ids = {a["id"] for a in data}
    assert a1["id"] in ids
    assert a2["id"] in ids


def test_alert_get_item(client):
    """GET single alert returns the alert."""
    shipment = create_shipment(client)
    alert = create_alert_via_reading(client, shipment["id"])

    resp = client.get(f"/api/shipments/{shipment['id']}/alerts/{alert['id']}")

    assert resp.status_code == 200
    assert resp.get_json()["id"] == alert["id"]


def test_alert_get_wrong_shipment_404(client):
    """GET alert returns 404 if shipment does not match."""
    s1 = create_shipment(client)
    s2 = create_shipment(client)
    alert = create_alert_via_reading(client, s1["id"])

    resp = client.get(f"/api/shipments/{s2['id']}/alerts/{alert['id']}")

    assert resp.status_code == 404


def test_alert_get_non_existing_404(client):
    """GET alert item returns 404 for unknown id."""
    shipment = create_shipment(client)

    resp = client.get(f"/api/shipments/{shipment['id']}/alerts/99999")

    assert resp.status_code == 404


def test_alerts_post_via_readings_201_and_location(client):
    """POST readings creates an alert and returns 201"""
    shipment = create_shipment(client)

    resp = client.post(
        f"/api/shipments/{shipment['id']}/readings",
        json={"temp": 10, "humidity": 30},
    )

    assert resp.status_code == 201
    body = resp.get_json()
    assert isinstance(body, list)
    assert len(body) == 2

    reading = body[0]
    alert = body[1]

    assert alert["shipment_id"] == shipment["id"]
    assert alert["reading_id"] == reading["id"]
    assert alert["severity"] == "warning"
    assert alert["is_resolved"] is False
    assert "out of range" in alert["msg"]


def test_alerts_post_via_readings_visible_in_alerts_get(client):
    """Alert created from POST readings is visible via GET alerts list."""
    shipment = create_shipment(client)

    post_resp = client.post(
        f"/api/shipments/{shipment['id']}/readings",
        json={"temp": 10, "humidity": 30},
    )
    created_alert = post_resp.get_json()[1]

    get_resp = client.get(f"/api/shipments/{shipment['id']}/alerts")

    assert get_resp.status_code == 200
    alerts = get_resp.get_json()
    assert any(a["id"] == created_alert["id"] for a in alerts)


def test_alert_put_updates(client):
    """PUT alert updates fields and returns updated alert."""
    shipment = create_shipment(client)
    alert = create_alert_via_reading(client, shipment["id"])

    resp = client.put(
        f"/api/shipments/{shipment['id']}/alerts/{alert['id']}",
        json={"msg": "Resolved", "severity": "critical", "is_resolved": True},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == alert["id"]
    assert body["msg"] == "Resolved"
    assert body["severity"] == "critical"
    assert body["is_resolved"] is True


def test_alert_put_415_no_json(client):
    """PUT alert returns 415 when body is not JSON."""
    shipment = create_shipment(client)
    alert = create_alert_via_reading(client, shipment["id"])

    resp = client.put(
        f"/api/shipments/{shipment['id']}/alerts/{alert['id']}",
        content_type="application/json",
        data="null",
    )

    assert resp.status_code == 415


def test_alert_put_400_schema_fail(client):
    """PUT alert returns 400 when schema validation fails."""
    shipment = create_shipment(client)
    alert = create_alert_via_reading(client, shipment["id"])

    resp = client.put(
        f"/api/shipments/{shipment['id']}/alerts/{alert['id']}",
        json={"is_resolved": "bad"},
    )

    assert resp.status_code == 400


def test_alert_put_wrong_shipment_400(client):
    """PUT alert returns 400 when alert does not belong to shipment."""
    s1 = create_shipment(client)
    s2 = create_shipment(client)
    alert = create_alert_via_reading(client, s1["id"])

    resp = client.put(
        f"/api/shipments/{s2['id']}/alerts/{alert['id']}",
        json={"msg": "x", "severity": "warning", "is_resolved": False},
    )

    assert resp.status_code == 400


def test_alert_put_404_when_alert_not_found(client):
    """PUT alert returns 404 when alert id does not exist."""
    shipment = create_shipment(client)

    resp = client.put(
        f"/api/shipments/{shipment['id']}/alerts/99999",
        json={"msg": "x", "severity": "warning", "is_resolved": False},
    )

    assert resp.status_code == 404


def test_alert_put_400_on_value_error(client, monkeypatch):
    """PUT alert returns 400 when deserialize raises ValueError."""
    shipment = create_shipment(client)
    alert = create_alert_via_reading(client, shipment["id"])

    def boom(*args, **kwargs):
        raise ValueError("bad")

    monkeypatch.setattr(Alert, "deserialize", boom)

    resp = client.put(
        f"/api/shipments/{shipment['id']}/alerts/{alert['id']}",
        json={"msg": "x", "severity": "warning", "is_resolved": False},
    )

    assert resp.status_code == 400

