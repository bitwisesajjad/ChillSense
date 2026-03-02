"""Tests for app factory configuration branches."""

from src import create_app


def test_create_app_without_test_config():
    """create_app() works without test_config and serves /health."""
    app = create_app()
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200