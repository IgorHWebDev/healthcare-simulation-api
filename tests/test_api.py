import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime
from api.main import app
from api.security.auth import create_token
from api.config.settings import settings

client = TestClient(app)

# Mock data
MOCK_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjk5OTk5OTk5OTl9.1234567890"
MOCK_API_KEY = "test-api-key"

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers():
    """Create valid authentication headers."""
    token = create_token({"sub": "test_user"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def api_key_headers():
    """Create valid API key headers."""
    return {"X-API-Key": settings.API_KEY}

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Healthcare Framework API"}

def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_encrypt_data(auth_headers):
    """Test data encryption endpoint."""
    data = {"data": "test data"}
    response = client.post("/v1/encrypt", json=data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "encrypted_data" in data
    assert "key_id" in data
    assert "expiry" in data

def test_encrypt_data_invalid_token():
    """Test encryption with invalid token."""
    data = {"data": "test data"}
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.post("/v1/encrypt", json=data, headers=headers)
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()

def test_get_metrics(api_key_headers):
    """Test metrics endpoint."""
    response = client.get("/metrics", headers=api_key_headers)
    assert response.status_code == 200
    data = response.json()
    assert "requests_total" in data
    assert "errors_total" in data
    assert "latency_ms" in data

def test_get_metrics_invalid_api_key():
    """Test metrics with invalid API key."""
    headers = {"X-API-Key": "invalid_key"}
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 403
    assert "invalid api key" in response.json()["detail"].lower() 