"""
Functional tests for Shipments API endpoints.
"""
from sqlalchemy.exc import IntegrityError
from src.extensions import db
from src.models import Shipment

def create_shipment(client, payload=None):
    """
    Create a shipment using POST /api/shipments.
    """
    if payload is None:
        payload = {
            "name": "S1",
            "origin": "Oulu",
            "destination": "Helsinki",
            "min_temperature": -10,
            "max_temperature": 5,
        }
    return client.post("/api/shipments", json=payload)


def test_shipments_get_empty(client):
    """GET /api/shipments should return an empty list when database is empty."""
    resp = client.get("/api/shipments")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_shipments_post_201_and_location(client):
    """POST /api/shipments should create a shipment and return 201 + Location header."""
    resp = create_shipment(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert "id" in body
    assert resp.headers["Location"] == f"/api/shipments/{body['id']}"


def test_shipment_get_item(client):
    """GET /api/shipments/<shipment> should return the created shipment."""
    created = create_shipment(client).get_json()
    resp = client.get(f"/api/shipments/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == created["id"]


def test_shipment_put_updates(client):
    """PUT /api/shipments/<shipment> should update fields and return the updated shipment."""
    created = create_shipment(client).get_json()
    payload = {
        "name": "S1-updated",
        "origin": "Oulu",
        "destination": "Tampere",
        "status": "active",
        "min_temperature": -20,
        "max_temperature": 2,
    }
    resp = client.put(f"/api/shipments/{created['id']}", json=payload)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["name"] == "S1-updated"
    assert body["destination"] == "Tampere"


def test_shipments_post_415_no_json(client):
    """POST /api/shipments with non-JSON content should return 415."""
    resp = client.post("/api/shipments", data="nope", content_type="text/plain")
    assert resp.status_code == 415


def test_shipments_post_400_schema_fail(client):
    """POST /api/shipments with missing required fields should return 400. """
    resp = client.post("/api/shipments", json={"name": "only-name"})
    assert resp.status_code == 400


def test_shipment_delete_403_without_key(client):
    """DELETE /api/shipments/<shipment> without API key should return 403."""
    created = create_shipment(client).get_json()
    resp = client.delete(f"/api/shipments/{created['id']}")
    assert resp.status_code == 403


def test_shipment_delete_204_with_key(client):
    """DELETE /api/shipments/<shipment> with a valid admin API key should return 204
    and the shipment should not be accessible after that."""
    created = create_shipment(client).get_json()
    resp = client.delete(
        f"/api/shipments/{created['id']}",
        headers={"Shipmenthub-Api-Key": "adminkey"},
    )
    assert resp.status_code == 204

    resp2 = client.get(f"/api/shipments/{created['id']}")
    assert resp2.status_code == 404

def test_shipments_post_409_on_integrityerror(client, monkeypatch):
    """POST /api/shipments returns 409 when DB commit show IntegrityError."""
    def boom():
        raise IntegrityError("stmt", "params", "orig")

    monkeypatch.setattr(db.session, "commit", boom)

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
    assert resp.status_code == 409


def test_shipments_post_400_on_valueerror(client, monkeypatch):
    """POST /api/shipments returns 400 when deserialize raises ValueError."""
    def boom(self, doc):
        raise ValueError("bad value")

    monkeypatch.setattr(Shipment, "deserialize", boom)

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
    assert resp.status_code == 400


def test_shipment_put_409_on_integrityerror(client, monkeypatch):
    """PUT /api/shipments/<id> returns 409 when DB commit raises IntegrityError."""
    created = create_shipment(client).get_json()

    def boom():
        raise IntegrityError("stmt", "params", "orig")

    monkeypatch.setattr(db.session, "commit", boom)

    resp = client.put(
        f"/api/shipments/{created['id']}",
        json={
            "name": "S1",
            "origin": "Oulu",
            "destination": "Helsinki",
            "min_temperature": -10,
            "max_temperature": 5,
        },
    )
    assert resp.status_code == 409


def test_shipment_put_400_on_valueerror(client, monkeypatch):
    """PUT /api/shipments/<id> returns 400 when deserialize raises ValueError."""
    created = create_shipment(client).get_json()

    def boom(self, doc):
        raise ValueError("bad value")

    monkeypatch.setattr(Shipment, "deserialize", boom)

    resp = client.put(
        f"/api/shipments/{created['id']}",
        json={
            "name": "S1",
            "origin": "Oulu",
            "destination": "Helsinki",
            "min_temperature": -10,
            "max_temperature": 5,
        },
    )
    assert resp.status_code == 400

def test_shipment_put_415_when_json_missing(client):
    """PUT shipment returns 415 when request body is not JSON."""
    created = create_shipment(client).get_json()

    resp = client.put(
        f"/api/shipments/{created['id']}",
        data="not-json",
        content_type="text/plain",
    )
    assert resp.status_code == 415


def test_shipment_put_400_when_data_invalid(client):
    """PUT shipment returns 400 when shipment data is invalid."""
    created = create_shipment(client).get_json()

    resp = client.put(
        f"/api/shipments/{created['id']}",
        json={
            "name": "S1",
            "origin": "Oulu",
            "destination": "Helsinki",
            "min_temperature": "bad",
            "max_temperature": 5,
        },
    )
    assert resp.status_code == 400