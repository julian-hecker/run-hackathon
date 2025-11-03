"""Tests for main app endpoints."""

from fastapi.testclient import TestClient

from voice_api.main import app


def test_root_endpoint():
    """Test that the root endpoint returns ok status."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
