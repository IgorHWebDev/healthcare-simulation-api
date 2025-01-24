import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
import os
import sys
from httpx import AsyncClient
import jwt

from api.main import app
from api.security.quantum import QuantumEncryption
from api.utils.audit import AuditLogger
from api.config.settings import settings

# Constants
MOCK_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdF91c2VyIiwicm9sZSI6ImhlYWx0aGNhcmVfcHJvdmlkZXIifQ.4jFDjGh_m4IG06Ri_uH3bJ-qKA2DfvZr9YgGJHf1r5g"
MOCK_PATIENT_ID = "P1234567890"

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.append(os.path.join(project_root, "api"))

# Test data
@pytest.fixture
def mock_phi_data():
    return {
        "patient_id": MOCK_PATIENT_ID,
        "data_type": "demographics",
        "content": {
            "name": "John Doe",
            "age": 45,
            "gender": "male"
        },
        "metadata": {
            "source": "test_suite"
        }
    }

@pytest.fixture
def mock_dicom_data():
    return {
        "patient_id": MOCK_PATIENT_ID,
        "study_uid": "1.2.3.4.5",
        "series_uid": "1.2.3.4.5.1",
        "image_data": b"mock_image_data",
        "metadata": {
            "modality": "CT",
            "study_date": "20240321"
        }
    }

@pytest.fixture
def mock_fhir_patient():
    return {
        "identifier": [{"system": "iqhis", "value": MOCK_PATIENT_ID}],
        "active": True,
        "name": [{"family": "Doe", "given": ["John"]}],
        "gender": "male",
        "birthDate": "1979-03-21"
    }

# Client fixtures
@pytest.fixture
def test_token():
    """Generate a valid test token."""
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def invalid_token():
    """Generate an invalid test token."""
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    return jwt.encode(payload, "invalid_secret", algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def auth_headers(test_token):
    """Get headers with valid authentication token."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def invalid_auth_headers(invalid_token):
    """Get headers with invalid authentication token."""
    return {"Authorization": f"Bearer {invalid_token}"}

@pytest.fixture
def client():
    """Get test client."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Get async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Component fixtures
@pytest.fixture
def quantum_encryption():
    """Fixture to provide quantum encryption instance."""
    return QuantumEncryption()

@pytest.fixture
def temp_log_dir():
    """Create temporary directory for audit logs"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def audit_logger(temp_log_dir):
    """Fixture to provide audit logger instance."""
    logger = AuditLogger()
    logger.log_dir = temp_log_dir
    logger.log_dir.mkdir(parents=True, exist_ok=True)
    logger.clear_logs()  # Clear logs before each test
    return logger

# Time-based fixtures
@pytest.fixture
def time_range():
    end = datetime.now()
    start = end - timedelta(days=1)
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat()
    }

# Error scenarios
@pytest.fixture
def invalid_patient_id():
    return "invalid_id"

# Performance testing
@pytest.fixture
def performance_thresholds():
    return {
        "phi_operation_ms": 200,
        "encryption_ms": 100,
        "audit_log_ms": 300
    }

# Compliance testing
@pytest.fixture
def hipaa_requirements():
    return {
        "encryption_required": True,
        "audit_required": True,
        "access_control_required": True,
        "data_integrity_required": True
    }

@pytest.fixture
def fda_requirements():
    return {
        "documentation_required": True,
        "validation_required": True,
        "verification_required": True,
        "traceability_required": True
    }

# Cleanup
@pytest.fixture(autouse=True)
def cleanup_logs(temp_log_dir):
    """Clean up logs after each test"""
    yield
    for log_file in temp_log_dir.glob("*.log"):
        log_file.unlink() 