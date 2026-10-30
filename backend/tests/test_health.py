from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_200():
    """Verify /api/v1/health endpoint responds with expected status and structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "store_backend" in data
    assert "forecast_mode" in data
    assert "timestamp" in data


def test_root_endpoint_returns_200():
    """Verify root endpoint provides links to docs and health."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "/api/v1/health" in data["health"]


def test_404_error_handler_format():
    """Verify global handling for nonexistent routes."""
    response = client.get("/api/v1/nonexistent-endpoint-xyz")
    assert response.status_code == 404
