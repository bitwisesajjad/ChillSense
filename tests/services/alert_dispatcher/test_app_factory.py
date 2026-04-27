"""Tests for alert-dispatcher app factory behavior."""

from services.alert_dispatcher import create_app


def test_create_app_uses_default_sqlite_and_serves_health(monkeypatch):
    """create_app() without test config uses default SQLite path and health endpoint."""
    monkeypatch.delenv("FLASK_DEBUG", raising=False)

    app = create_app()
    assert app.config["SQLALCHEMY_DATABASE_URI"].endswith("/alert_dispatcher.db")

    resp = app.test_client().get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_create_app_exposes_openapi_when_flask_debug_enabled(monkeypatch, tmp_path):
    """FLASK_DEBUG=1 enables Swagger/OpenAPI routes."""
    monkeypatch.setenv("FLASK_DEBUG", "1")

    db_file = tmp_path / "alert_dispatcher_test.db"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        }
    )

    resp = app.test_client().get("/openapi.yaml")
    assert resp.status_code == 200
    assert resp.mimetype == "application/yaml"
    assert b"openapi:" in resp.data
