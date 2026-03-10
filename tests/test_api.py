"""Tests for API-level routing and error handling."""


def test_unknown_api_route_returns_404(client):
    """Unknown API route returns 404."""
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404


def test_method_not_allowed_returns_405(client):
    """Unsupported HTTP method returns 405."""
    resp = client.patch("/api/shipments")
    assert resp.status_code == 405


def test_unknown_root_route_returns_404(client):
    """Unknown non-API route returns 404."""
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404