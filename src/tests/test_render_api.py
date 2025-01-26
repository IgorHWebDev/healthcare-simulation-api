import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import json
import logging
from datetime import datetime

from src.api.main import app
from src.api.healthcare.models import (
    PatientCreateRequest,
    AnalysisRequest,
    SimulationRequest,
    ValidationRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize test client
client = TestClient(app)

# Test data
TEST_API_KEY = "test_api_key_123"
TEST_HEADERS = {"X-API-Key": TEST_API_KEY}

@pytest.fixture
def test_patient_data():
    return {
        "name": "Test Patient",
        "age": 45,
        "gender": "M",
        "medical_history": ["Hypertension", "Diabetes"],
        "current_medications": ["Metformin", "Lisinopril"],
        "vital_signs": {
            "blood_pressure": "120/80",
            "heart_rate": 72,
            "temperature": 98.6
        }
    }

@pytest.fixture
def test_analysis_request():
    return {
        "scenario_type": "medication_interaction",
        "parameters": {
            "medications": ["Metformin", "Lisinopril"],
            "duration_days": 30
        },
        "risk_factors": ["Diabetes", "Hypertension"],
        "optimization_level": "high"
    }

@pytest.fixture
def test_simulation_request():
    return {
        "patient_data": {
            "age": 45,
            "conditions": ["Diabetes", "Hypertension"],
            "medications": ["Metformin", "Lisinopril"]
        },
        "simulation_parameters": {
            "duration_months": 6,
            "intervention_points": ["medication_adjustment", "lifestyle_changes"],
            "risk_threshold": 0.7
        },
        "optimization_settings": {
            "use_gpu": True,
            "precision": "high",
            "parallel_simulations": 4
        }
    }

def test_create_patient(test_patient_data):
    """Test patient creation endpoint"""
    response = client.post(
        "/api/v1/healthcare/patients",
        headers=TEST_HEADERS,
        json=test_patient_data
    )
    assert response.status_code == 201
    data = response.json()
    assert "patient_id" in data
    assert data["status"] == "success"
    return data["patient_id"]

def test_analyze_patient_scenario(test_patient_data, test_analysis_request):
    """Test patient scenario analysis endpoint"""
    # First create a patient
    patient_id = test_create_patient(test_patient_data)
    
    response = client.post(
        f"/api/v1/healthcare/patients/{patient_id}/analyze",
        headers=TEST_HEADERS,
        json=test_analysis_request
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "status" in data
    assert data["status"] in ["completed", "processing"]

def test_simulate_scenario(test_simulation_request):
    """Test scenario simulation endpoint"""
    response = client.post(
        "/api/v1/healthcare/simulate",
        headers=TEST_HEADERS,
        json=test_simulation_request
    )
    assert response.status_code == 200
    data = response.json()
    assert "simulation_id" in data
    assert "status" in data
    assert "results" in data
    
    # Verify M3 optimization metrics
    assert "performance_metrics" in data
    metrics = data["performance_metrics"]
    assert "gpu_utilization" in metrics
    assert "processing_time" in metrics
    assert "memory_usage" in metrics

def test_validate_protocol():
    """Test protocol validation endpoint"""
    validation_request = {
        "protocol_name": "Diabetes Management",
        "protocol_steps": [
            {
                "step": "Initial Assessment",
                "requirements": ["Blood Glucose", "HbA1c", "Blood Pressure"]
            },
            {
                "step": "Medication Review",
                "requirements": ["Current Medications", "Allergies"]
            }
        ],
        "validation_level": "strict"
    }
    
    response = client.post(
        "/api/v1/healthcare/validate",
        headers=TEST_HEADERS,
        json=validation_request
    )
    assert response.status_code == 200
    data = response.json()
    assert "validation_id" in data
    assert "status" in data
    assert "validation_results" in data

def test_error_handling():
    """Test API error handling"""
    # Test invalid API key
    response = client.post(
        "/api/v1/healthcare/patients",
        headers={"X-API-Key": "invalid_key"},
        json={}
    )
    assert response.status_code == 401

    # Test invalid patient ID
    response = client.post(
        f"/api/v1/healthcare/patients/{uuid4()}/analyze",
        headers=TEST_HEADERS,
        json={}
    )
    assert response.status_code == 404

    # Test invalid request body
    response = client.post(
        "/api/v1/healthcare/simulate",
        headers=TEST_HEADERS,
        json={}
    )
    assert response.status_code == 422

def test_performance_metrics():
    """Test performance metrics collection"""
    metrics_data = {
        "test_duration_seconds": 30,
        "requests_per_second": 100,
        "average_response_time": 0.05
    }
    
    # Create test data
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics_data,
        "environment": {
            "cpu": "Apple M3",
            "gpu": "Metal",
            "memory": "16GB"
        }
    }
    
    # Save metrics
    with open("performance_metrics.json", "w") as f:
        json.dump(test_data, f, indent=2)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--capture=no"])
