import pytest
import os
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["API_KEY"] = "test_api_key_123"
    os.environ["DB_USER"] = "test_user"
    os.environ["DB_PASSWORD"] = "test_password"
    os.environ["DB_NAME"] = "test_db"
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_PORT"] = "5432"
    
    # Clean up after tests
    yield
    os.environ.pop("API_KEY", None)
    os.environ.pop("DB_USER", None)
    os.environ.pop("DB_PASSWORD", None)
    os.environ.pop("DB_NAME", None)
    os.environ.pop("DB_HOST", None)
    os.environ.pop("DB_PORT", None)

@pytest.fixture
def test_client():
    """Create a test client with proper authentication"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Get authentication headers"""
    return {"X-API-Key": os.getenv("API_KEY")}

@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    class MockSession:
        def __init__(self):
            self.committed = False
            self.rolled_back = False
        
        def commit(self):
            self.committed = True
        
        def rollback(self):
            self.rolled_back = True
        
        def close(self):
            pass
    
    return MockSession()

@pytest.fixture
def mock_patient_data():
    """Mock patient data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Test Patient",
        "age": 45,
        "gender": "M",
        "medical_history": ["Hypertension", "Diabetes"],
        "medications": ["Metformin", "Lisinopril"]
    }
