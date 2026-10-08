"""
Unit tests for health and basic application endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that GET / returns a 200 OK and documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert "health" in data
    assert "version" in data


def test_health_check_endpoint():
    """Verify that GET /health returns service status and diagnostic information."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "database" in data
