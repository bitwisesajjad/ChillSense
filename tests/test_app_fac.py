"""Tests for app factory configuration branches."""

from src import create_app


def test_create_app_without_test_config():
    """create_app() works without test_config and serves /health."""
    app = create_app()
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200


def test_create_app_exposes_openapi_when_debug_enabled(tmp_path):
    """DEBUG=True enables OpenAPI route in the main app."""
    db_file = tmp_path / "main_api_test.db"
    app = create_app(
        {
            "TESTING": True,
            "DEBUG": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        }
    )

    resp = app.test_client().get("/openapi.yaml")
    assert resp.status_code == 200
    assert resp.mimetype == "application/yaml"
    assert b"openapi:" in resp.data