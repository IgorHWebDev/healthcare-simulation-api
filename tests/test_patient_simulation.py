"""
Test suite for patient simulation scenarios using LM Studio healthcare model.
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
import json
from fastapi.testclient import TestClient
import httpx
import asyncio
from unittest.mock import patch, MagicMock
import jwt
from sqlalchemy import create_engine, text

from src.api.main import app
from src.api.healthcare.models import (
    PatientData,
    VitalSigns,
    LabResult,
    AnalysisRequest,
    ClinicalPrediction
)
from src.api.healthcare.operations import HealthcareOperations
from src.api.security.auth import create_access_token

# Test client setup
client = TestClient(app)

# Initialize healthcare operations
DATABASE_URL = "postgresql://healthcare:test@localhost:5432/healthcare_test"
app.state.healthcare_ops = HealthcareOperations(DATABASE_URL)

# API authentication headers
API_KEY = "test_api_key"
JWT_TOKEN = create_access_token({"sub": "test_user", "role": "admin"})
headers = {
    "X-API-Key": API_KEY,
    "Authorization": f"Bearer {JWT_TOKEN}"
}

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up the test database before each test."""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Disable foreign key checks
        conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        
        # Delete all data from tables
        conn.execute(text("DELETE FROM clinical_predictions"))
        conn.execute(text("DELETE FROM lab_results"))
        conn.execute(text("DELETE FROM medications"))
        conn.execute(text("DELETE FROM diagnoses"))
        conn.execute(text("DELETE FROM vital_signs"))
        conn.execute(text("DELETE FROM patients"))
        
        # Re-enable foreign key checks
        conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        conn.commit()

def get_test_patient_data(mrn=None):
    """Get test patient data with optional custom MRN."""
    return {
        "patient_data": {
            "mrn": mrn or f"MRN{uuid4().hex[:8].upper()}",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1960-01-15",
            "age": 65,
            "gender": "M",
            "vital_signs": {
                "blood_pressure": "140/90",
                "heart_rate": 80,
                "temperature": 37.2,
                "respiratory_rate": 16,
                "oxygen_saturation": 96
            },
            "conditions": [
                {
                    "icd_code": "I10",
                    "description": "Essential hypertension"
                },
                {
                    "icd_code": "E11.9",
                    "description": "Type 2 diabetes without complications"
                }
            ],
            "medications": [
                {
                    "medication_name": "metformin",
                    "dosage": "1000mg",
                    "frequency": "twice daily"
                },
                {
                    "medication_name": "lisinopril",
                    "dosage": "10mg",
                    "frequency": "once daily"
                }
            ],
            "lab_results": [
                {
                    "test_name": "HbA1c",
                    "value": 7.2,
                    "unit": "%",
                    "reference_range": "4.0-5.6",
                    "test_date": datetime.now().isoformat()
                },
                {
                    "test_name": "Blood Glucose",
                    "value": 142,
                    "unit": "mg/dL",
                    "reference_range": "70-99",
                    "test_date": datetime.now().isoformat()
                }
            ]
        }
    }

@pytest.fixture
def mock_lm_studio():
    """Mock LM Studio healthcare model responses."""
    with patch("src.api.healthcare.operations.HealthcareOperations._perform_deep_analysis") as mock:
        mock.return_value = {
            "predictions": {
                "risk_level": "moderate",
                "confidence": 0.85,
                "probability": 0.75
            },
            "recommendations": [
                "Consider adding aspirin therapy",
                "Increase physical activity",
                "Monitor blood pressure daily",
                "Schedule follow-up in 3 months"
            ],
            "risk_factors": [
                "Hypertension",
                "Type 2 Diabetes",
                "Age > 60",
                "Family history of cardiovascular disease",
                "Sedentary lifestyle"
            ],
            "type": "comprehensive_analysis"
        }
        yield mock

@pytest.mark.asyncio
async def test_complete_patient_simulation(mock_lm_studio):
    """Test complete patient simulation cycle."""
    # Create patient
    response = client.post(
        "/api/v1/healthcare/patients",
        headers={"X-API-Key": "test_api_key"},
        json=get_test_patient_data()
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert "patient_id" in response.json()["data"]

    # Get patient ID from response
    patient_id = response.json()["data"]["patient_id"]

    # Test patient scenario analysis
    response = client.post(
        f"/api/v1/healthcare/analyze/{patient_id}",
        headers={"X-API-Key": "test_api_key"},
        json={
            "patient_ids": [patient_id],
            "analysis_type": "risk_assessment"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "analysis" in response.json()["data"]

@pytest.mark.asyncio
async def test_patient_simulation_with_complications():
    """Test simulation with patient complications."""
    # Create patient with complications
    patient_data = get_test_patient_data()
    patient_data["patient_data"]["conditions"].append({
        "icd_code": "I50.9",
        "description": "Heart failure, unspecified"
    })
    patient_data["patient_data"]["vital_signs"]["oxygen_saturation"] = 92
    
    response = client.post(
        "/api/v1/healthcare/patients",
        headers={"X-API-Key": "test_api_key"},
        json=patient_data
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert "patient_id" in response.json()["data"]

    # Get patient ID from response
    patient_id = response.json()["data"]["patient_id"]

    # Test patient scenario analysis with complications
    response = client.post(
        f"/api/v1/healthcare/analyze/{patient_id}",
        headers={"X-API-Key": "test_api_key"},
        json={
            "patient_ids": [patient_id],
            "analysis_type": "complication_risk"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "analysis" in response.json()["data"]

@pytest.mark.asyncio
async def test_patient_simulation_with_treatment_response():
    """Test simulation with treatment response analysis."""
    # Create patient with treatment history
    response = client.post(
        "/api/v1/healthcare/patients",
        headers={"X-API-Key": "test_api_key"},
        json=get_test_patient_data()
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert "patient_id" in response.json()["data"]

    # Get patient ID from response
    patient_id = response.json()["data"]["patient_id"]

    # Test patient scenario analysis with treatment response
    response = client.post(
        f"/api/v1/healthcare/analyze/{patient_id}",
        headers={"X-API-Key": "test_api_key"},
        json={
            "patient_ids": [patient_id],
            "analysis_type": "treatment_response"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "analysis" in response.json()["data"]
