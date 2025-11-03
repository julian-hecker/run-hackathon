"""Tests for health check endpoints."""

from fastapi.testclient import TestClient

from voice_api.main import app


def test_health_endpoint():
    """Test that the health endpoint returns ok status."""
    client = TestClient(app)
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

