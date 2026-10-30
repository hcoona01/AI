"""Integration tests for the forecast API endpoints and RBAC."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)

ADMIN_HEADERS = {"x-user-role": "admin", "x-user-id": "u-admin-test"}
FACULTY_HEADERS = {
    "x-user-role": "faculty",
    "x-user-id": "u-faculty-test",
    "x-faculty-id": "f-01",
}


def test_forecast_run_requires_admin():
    """Faculty cannot trigger forecast/run (403 forbidden)."""
    resp = client.post("/api/v1/forecast/run", json={}, headers=FACULTY_HEADERS)
    assert resp.status_code == 403


def test_forecast_run_unauthenticated():
    """Unauthenticated request is rejected (401)."""
    resp = client.post("/api/v1/forecast/run", json={})
    assert resp.status_code == 401


def test_forecast_run_admin_succeeds():
    """Admin can trigger forecast/run and get valid ForecastRunResponse."""
    resp = client.post(
        "/api/v1/forecast/run",
        json={"term": "Fall 2026"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["term"] == "Fall 2026"
    assert data["courses_forecasted"] > 0
    assert data["forecast_mode"] in ("model", "precomputed")


def test_forecast_get_authenticated():
    """Authenticated user (faculty or admin) can read forecasts."""
    # Read as faculty
    resp = client.get("/api/v1/forecast?term=Fall%202026", headers=FACULTY_HEADERS)
    assert resp.status_code == 200
    records = resp.json()
    assert isinstance(records, list)
    assert len(records) > 0

    first = records[0]
    assert "course_id" in first
    assert "p10" in first
    assert "p50" in first
    assert "p90" in first
    assert first["p10"] <= first["p50"] <= first["p90"]


def test_forecast_run_missing_artifacts_returns_503(monkeypatch):
    """If artifacts are missing in model mode, returns 503."""
    from pathlib import Path

    fake_dir = Path("non_existent_artifacts_dir_12345")
    monkeypatch.setattr("app.services.forecast_service.ARTIFACTS_DIR", fake_dir)
    monkeypatch.setattr(settings, "FORECAST_MODE", "model")

    resp = client.post("/api/v1/forecast/run", json={}, headers=ADMIN_HEADERS)
    assert resp.status_code == 503
    body = resp.json()
    assert "make train" in body["message"]

