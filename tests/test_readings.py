"""
Functional tests for Readings API endpoints.

Readings are nested under shipments:
- /api/shipments/<shipment>/readings
- /api/shipments/<shipment>/readings/<reading>
"""


def create_shipment(client):
    """
    Create a shipment for readings tests.
    """
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
    """
    Create a reading under a shipment using POST /api/shipments/<shipment>/readings.

    Args:
        client: Flask test client.
        shipment_id: Shipment id for the nested resource.
        payload: Optional JSON payload. If not provided, a valid default is used.

    Returns:
        Flask response object.
    """
    if payload is None:
        payload = {"temp": -5, "humidity": 30}
    return client.post(f"/api/shipments/{shipment_id}/readings", json=payload)


def test_readings_post_201_and_location(client):
    """
    POST /api/shipments/<shipment>/readings should return 201 + Location header.
    """
    shipment = create_shipment(client)
    resp = create_reading(client, shipment["id"])
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["shipment_id"] == shipment["id"]
    assert resp.headers["Location"] == (
        f"/api/shipments/{shipment['id']}/readings/{body['id']}"
    )


def test_readings_get_list(client):
    """
    GET /api/shipments/<shipment>/readings should list readings for that shipment.
    """
    shipment = create_shipment(client)
    create_reading(client, shipment["id"])
    resp = client.get(f"/api/shipments/{shipment['id']}/readings")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_reading_get_item(client):
    """
    GET /api/shipments/<shipment>/readings/<reading> should return the reading.
    """
    shipment = create_shipment(client)
    reading = create_reading(client, shipment["id"]).get_json()
    resp = client.get(f"/api/shipments/{shipment['id']}/readings/{reading['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == reading["id"]


def test_reading_get_wrong_shipment_404(client):
    """
    A reading must not be accessible through a different shipment id (should be 404).
    """
    s1 = create_shipment(client)
    s2 = client.post(
        "/api/shipments",
        json={"name": "S2", "origin": "A", "destination": "B"},
    ).get_json()

    reading = create_reading(client, s1["id"]).get_json()
    resp = client.get(f"/api/shipments/{s2['id']}/readings/{reading['id']}")
    assert resp.status_code == 404


def test_reading_put_updates(client):
    """
    PUT /api/shipments/<shipment>/readings/<reading> should update the reading.
    """
    shipment = create_shipment(client)
    reading = create_reading(client, shipment["id"]).get_json()

    resp = client.put(
        f"/api/shipments/{shipment['id']}/readings/{reading['id']}",
        json={"temp": 2, "humidity": None},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["temp"] == 2.0
    assert body["humidity"] is None


def test_readings_post_415_no_json(client):
    """
    POST /api/shipments/<shipment>/readings with non-JSON content should return 415.
    """
    shipment = create_shipment(client)
    resp = client.post(
        f"/api/shipments/{shipment['id']}/readings",
        data="nope",
        content_type="text/plain",
    )
    assert resp.status_code == 415

def test_readings_post_400_schema_fail(client):
    """
    POST /api/shipments/<shipment>/readings with missing fields should return 400.
    """
    shipment = create_shipment(client)
    resp = client.post(f"/api/shipments/{shipment['id']}/readings", json={})
    assert resp.status_code == 400
