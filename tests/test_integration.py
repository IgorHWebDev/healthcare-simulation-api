"""Integration tests for Healthcare Simulation API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.env_loader import EnvironmentLoader

env = EnvironmentLoader()
client = TestClient(app)

@pytest.fixture
def api_key():
    """Get test API key."""
    return env.get('DEFAULT_API_KEY', 'test_key')

@pytest.fixture
def headers(api_key):
    """Get test headers."""
    return {
        'X-RapidAPI-Key': api_key,
        'Content-Type': 'application/json'
    }

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_simulate_scenario(headers):
    """Test simulation endpoint."""
    payload = {
        "message": "Start cardiac arrest simulation",
        "language": "en"
    }
    response = client.post("/simulate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "scenario_id" in data
    assert "response" in data
    assert "next_steps" in data
    assert len(data["next_steps"]) > 0

def test_validate_action(headers):
    """Test validation endpoint."""
    payload = {
        "action": "Start chest compressions",
        "protocol": "ACLS"
    }
    response = client.post("/validate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "feedback" in data
    assert isinstance(data["score"], (int, float))

def test_invalid_api_key():
    """Test invalid API key handling."""
    headers = {
        'X-RapidAPI-Key': 'invalid_key',
        'Content-Type': 'application/json'
    }
    payload = {"message": "Test simulation"}
    response = client.post("/simulate", json=payload, headers=headers)
    assert response.status_code == 401

def test_invalid_request():
    """Test invalid request handling."""
    headers = {
        'X-RapidAPI-Key': 'test_key',
        'Content-Type': 'application/json'
    }
    payload = {}  # Missing required fields
    response = client.post("/simulate", json=payload, headers=headers)
    assert response.status_code == 422 