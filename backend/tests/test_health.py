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


def test_root_health_check_returns_200():
    """Verify root /health endpoint used by cloud health checkers responds with 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Faculty Workload Balancing API"


def test_security_headers_present():
    """Verify production security headers are attached across responses."""
    response = client.get("/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


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
