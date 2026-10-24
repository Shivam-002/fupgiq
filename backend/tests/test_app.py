from datetime import date
from typing import Annotated

import httpx
import pytest
from fastapi import Query
from fastapi.testclient import TestClient

from app.core.exceptions import ProviderUnavailableError
from app.main import create_app

FRONTEND = "http://localhost:5173"


@pytest.fixture
def client() -> TestClient:
    app = create_app()

    @app.get("/api/test/app-error")
    def app_error() -> None:
        raise ProviderUnavailableError()

    @app.get("/api/test/crash")
    def crash() -> None:
        raise RuntimeError("secret internal detail")

    @app.get("/api/test/validated")
    def validated(day: Annotated[date, Query()]) -> dict[str, str]:
        return {"day": day.isoformat()}

    return TestClient(app, raise_server_exceptions=False)


def assert_error(response: httpx.Response, status: int, code: str) -> None:
    assert response.status_code == status
    body = response.json()
    assert list(body) == ["error"]
    assert body["error"]["code"] == code
    assert body["error"]["message"]


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_standard_404(client: TestClient) -> None:
    assert_error(client.get("/api/does-not-exist"), 404, "NOT_FOUND")


def test_wrong_method_returns_standard_405(client: TestClient) -> None:
    assert_error(client.post("/api/health"), 405, "METHOD_NOT_ALLOWED")


def test_app_error_keeps_its_status_and_code(client: TestClient) -> None:
    assert_error(client.get("/api/test/app-error"), 503, "PROVIDER_UNAVAILABLE")


def test_missing_param_returns_standard_422(client: TestClient) -> None:
    response = client.get("/api/test/validated")
    assert_error(response, 422, "INVALID_REQUEST")
    assert response.json()["error"]["message"].startswith("day")


def test_malformed_param_returns_standard_422(client: TestClient) -> None:
    assert_error(client.get("/api/test/validated?day=not-a-date"), 422, "INVALID_REQUEST")


def test_unexpected_crash_returns_clean_500_with_cors(client: TestClient) -> None:
    response = client.get("/api/test/crash", headers={"Origin": FRONTEND})
    assert_error(response, 500, "INTERNAL_ERROR")
    assert "secret internal detail" not in response.text
    assert response.headers["access-control-allow-origin"] == FRONTEND


def test_cors_allows_frontend_only(client: TestClient) -> None:
    allowed = client.get("/api/health", headers={"Origin": FRONTEND})
    blocked = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert allowed.headers["access-control-allow-origin"] == FRONTEND
    assert "access-control-allow-origin" not in blocked.headers
