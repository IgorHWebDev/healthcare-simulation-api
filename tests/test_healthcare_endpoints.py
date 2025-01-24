import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient
from api.main import app
from api.security.quantum import QuantumEncryption
from api.utils.audit import AuditLogger
from api.security.auth import create_token
from api.config.settings import settings

client = TestClient(app)

# Mock data
MOCK_PATIENT_ID = "P1234567890"
MOCK_PHI_DATA = {
    "patient_id": MOCK_PATIENT_ID,
    "data_type": "clinical_note",
    "content": {
        "note": "Test clinical note"
    }
}

@pytest.fixture
def auth_headers():
    """Create valid authentication headers."""
    token = create_token({"sub": "test_user"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def api_key_headers():
    """Create valid API key headers."""
    return {"X-API-Key": settings.API_KEY}

@pytest.fixture
def async_client():
    return TestClient(app)

@pytest.fixture
def audit_logger():
    logger = AuditLogger()
    logger.clear_logs()  # Clear logs before each test
    return logger

@pytest.fixture
def quantum_encryption():
    return QuantumEncryption()

@pytest.fixture(autouse=True)
def clear_audit_logs():
    """Clear audit logs before each test."""
    audit_logger = AuditLogger()
    audit_logger.clear_logs()
    yield
    audit_logger.clear_logs()

class TestPHIEndpoints:
    """Test suite for PHI handling endpoints"""

    def test_store_phi_success(self, async_client, auth_headers):
        """Test successful PHI storage"""
        data = {
            "patient_id": MOCK_PATIENT_ID,
            "data_type": "clinical_note",
            "content": {"note": "Test clinical note"}
        }
        response = async_client.post("/v1/healthcare/phi/store", json=data, headers=auth_headers)
        print(f"Response data: {response.json()}")
        assert response.status_code == 200
        response_data = response.json()
        assert "id" in response_data
        assert response_data["patient_id"] == MOCK_PATIENT_ID
        assert response_data["id"].startswith(f"PHI_{MOCK_PATIENT_ID}")

    def test_store_phi_invalid_data(self, async_client, auth_headers):
        """Test PHI storage with invalid data"""
        data = {
            "patient_id": "invalid",
            "data_type": "clinical_note",
            "content": {"note": "Test clinical note"}
        }
        response = async_client.post("/v1/healthcare/phi/store", json=data, headers=auth_headers)
        assert response.status_code == 422

    def test_store_phi_unauthorized(self, async_client):
        """Test PHI storage without authorization"""
        data = {
            "patient_id": MOCK_PATIENT_ID,
            "data_type": "clinical_note",
            "content": {"note": "Test clinical note"}
        }
        response = async_client.post("/v1/healthcare/phi/store", json=data)
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_retrieve_phi_success(self, async_client, auth_headers):
        """Test successful PHI retrieval"""
        record_id = f"PHI_{MOCK_PATIENT_ID}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        response = async_client.get(
            f"/v1/healthcare/phi/retrieve?patient_id={MOCK_PATIENT_ID}&record_id={record_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == record_id
        assert response_data["patient_id"] == MOCK_PATIENT_ID

    def test_retrieve_phi_invalid_id(self, async_client, auth_headers):
        """Test PHI retrieval with invalid patient ID"""
        record_id = f"PHI_{MOCK_PATIENT_ID}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        response = async_client.get(
            f"/v1/healthcare/phi/retrieve?patient_id={MOCK_PATIENT_ID}&record_id=invalid_id",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "invalid record id format" in response.json()["detail"].lower()

    def test_audit_logs_success(self, async_client, auth_headers):
        """Test successful audit log retrieval"""
        response = async_client.get(
            f"/v1/healthcare/phi/audit?patient_id={MOCK_PATIENT_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        response_data = response.json()
        assert "logs" in response_data
        assert isinstance(response_data["logs"], list)

class TestQuantumEncryption:
    """Test suite for quantum encryption functionality"""

    def test_encryption_decryption(self, quantum_encryption):
        """Test that encryption and decryption work correctly."""
        test_data = "test data"
        
        # Test encryption
        encrypted = quantum_encryption.encrypt(test_data)
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        
        # Test decryption
        decrypted = quantum_encryption.decrypt(encrypted)
        assert decrypted == test_data

    def test_key_rotation(self, quantum_encryption):
        """Test that key rotation works correctly."""
        old_key_id = quantum_encryption.current_key_id
        quantum_encryption.rotate_key()
        new_key_id = quantum_encryption.current_key_id
        
        assert old_key_id != new_key_id
        assert new_key_id.startswith("qk_")
        assert len(new_key_id) > 16  # Basic format check

class TestAuditLogger:
    """Test suite for audit logging functionality"""

    @pytest.mark.asyncio
    async def test_log_access(self, audit_logger):
        """Test access logging"""
        await audit_logger.log_access(
            user_id="test_user",
            patient_id=MOCK_PATIENT_ID,
            action="read",
            resource_type="phi",
            resource_id="test_record"
        )
        
        # Verify logs were created
        logs = await audit_logger.get_logs(patient_id=MOCK_PATIENT_ID)
        assert len(logs) == 1
        assert logs[0]["action"] == "read"

    @pytest.mark.asyncio
    async def test_log_filtering(self, audit_logger):
        # Create test logs
        await audit_logger.log_access(
            user_id="test_user",
            patient_id=MOCK_PATIENT_ID,
            action="write",
            resource_type="phi",
            resource_id="test_record_1"
        )
        await audit_logger.log_access(
            user_id="test_user",
            patient_id=MOCK_PATIENT_ID,
            action="read",
            resource_type="phi",
            resource_id="test_record_2"
        )

        # Filter logs by action
        write_logs = await audit_logger.get_logs(action="write")
        assert len(write_logs) == 1
        assert write_logs[0]["action"] == "write"

        read_logs = await audit_logger.get_logs(action="read")
        assert len(read_logs) == 1
        assert read_logs[0]["action"] == "read"

if __name__ == "__main__":
    pytest.main(["-v"]) 