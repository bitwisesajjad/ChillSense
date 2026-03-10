"""Tests for the Readings API endpoints."""

from src.models import Reading


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


def create_reading(client, shipment_id, payload=None):
    """Create a reading and return the created reading dict."""
    if payload is None:
        payload = {"temp": 10, "humidity": 30}

    resp = client.post(f"/api/shipments/{shipment_id}/readings", json=payload)
    data = resp.get_json()

    if isinstance(data, list):
        return data[0]

    return data


def test_readings_post_201_and_location(client):
    """POST readings returns 201 and Location header."""
    shipment = create_shipment(client)

    resp = client.post(
        f"/api/shipments/{shipment['id']}/readings",
        json={"temp": 10, "humidity": 30},
    )

    assert resp.status_code == 201
    body = resp.get_json()
    reading = body[0] if isinstance(body, list) else body

    assert "Location" in resp.headers
    assert resp.headers["Location"] == (
        f"/api/shipments/{shipment['id']}/readings/{reading['id']}"
    )


def test_readings_get_list(client):
    """GET readings list returns readings for a shipment."""
    shipment = create_shipment(client)
    create_reading(client, shipment["id"])

    resp = client.get(f"/api/shipments/{shipment['id']}/readings")

    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_reading_get_item(client):
    """GET single reading returns the reading."""
    shipment = create_shipment(client)
    reading = create_reading(client, shipment["id"])

    resp = client.get(
        f"/api/shipments/{shipment['id']}/readings/{reading['id']}"
    )

    assert resp.status_code == 200
    assert resp.get_json()["id"] == reading["id"]


def test_reading_get_wrong_shipment_404(client):
    """GET reading returns 404 if shipment does not match."""
    s1 = create_shipment(client)
    s2 = create_shipment(client)
    reading = create_reading(client, s1["id"])

    resp = client.get(
        f"/api/shipments/{s2['id']}/readings/{reading['id']}"
    )

    assert resp.status_code == 404


def test_readings_post_415_no_json(client):
    """POST readings returns 415 when body is not JSON."""
    shipment = create_shipment(client)

    resp = client.post(
        f"/api/shipments/{shipment['id']}/readings",
        data="not-json",
        content_type="text/plain",
    )

    assert resp.status_code == 415


def test_readings_post_400_schema_fail(client):
    """POST readings returns 400 when schema validation fails."""
    shipment = create_shipment(client)

    resp = client.post(
        f"/api/shipments/{shipment['id']}/readings",
        json={"temp": "bad"},
    )

    assert resp.status_code == 400


def test_reading_get_404_when_shipment_mismatch(client):
    """GET reading returns 404 when reading belongs to another shipment."""
    s1 = create_shipment(client)
    s2 = create_shipment(client)
    reading = create_reading(client, s1["id"])

    resp = client.get(
        f"/api/shipments/{s2['id']}/readings/{reading['id']}"
    )

    assert resp.status_code == 404


def test_readings_post_400_on_valueerror(client, monkeypatch):
    """POST readings returns 400 when deserialize raises ValueError."""
    shipment = create_shipment(client)

    def boom(*args, **kwargs):
        raise ValueError("bad")

    monkeypatch.setattr(Reading, "deserialize", boom)

    resp = client.post(
        f"/api/shipments/{shipment['id']}/readings",
        json={"temp": 10, "humidity": 30},
    )

    assert resp.status_code == 400