"""Tests for the versioned HTTP boundary."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from data_model_auditor.bootstrap.api import create_app
from data_model_auditor.bootstrap.settings import Settings
from data_model_auditor.infrastructure.http.errors import register_exception_handlers


def _client() -> TestClient:
    settings = Settings.from_environ({"APP_ENV": "homologation", "API_PORT": "8001"})
    return TestClient(create_app(settings))


def test_health_is_available_on_the_versioned_path() -> None:
    """The API exposes a health check and does not require a database."""
    response = _client().get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_path_uses_the_error_contract() -> None:
    """Missing routes return the same error shape as the other failures."""
    response = _client().get("/api/v1/missing")

    assert response.status_code == 404
    assert response.json() == {
        "code": "http_error",
        "message": "Not Found",
        "details": [],
    }


def test_unexpected_failure_hides_the_exception_text() -> None:
    """An internal failure is logged and returned without the exception content."""
    app = create_app(Settings.from_environ({}))

    @app.get("/api/v1/fail")
    def fail() -> dict[str, str]:
        raise RuntimeError("database password")

    response = TestClient(app, raise_server_exceptions=False).get("/api/v1/fail")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal_error"
    assert "database password" not in response.text


def test_validation_error_uses_the_error_contract() -> None:
    """Invalid input is reported with the standard error body."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/api/v1/checked")
    def checked(limit: int) -> dict[str, int]:
        return {"limit": limit}

    response = TestClient(app).get("/api/v1/checked", params={"limit": "many"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "invalid_request"
    assert body["details"]
