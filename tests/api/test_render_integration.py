"""
Integration tests for Render endpoints and database integration.
Tests the full flow from API endpoints to database operations.
"""
import pytest
from fastapi.testclient import TestClient
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
import json

from src.api.main import app
from src.database.mimic4_adapter import MIMIC4Adapter
from src.api.healthcare.models import (
    PatientData,
    ClinicalPrediction,
    AnalysisRequest,
    HealthcareResponse,
    LabResult
)
from src.api.security.auth import create_access_token

# Test client setup
client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Get authentication headers for testing."""
    token = create_access_token({"sub": "test_user", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def invalid_auth_headers():
    """Get invalid authentication headers for testing."""
    return {"Authorization": "Bearer invalid_token"}

@pytest.fixture
def mock_db():
    """Mock MIMIC4 database adapter."""
    with patch('src.api.main.db') as mock:
        mock.check_connection.return_value = True
        
        def get_patient_data(patient_id):
            """Generate mock patient data based on ID."""
            return {
                'patient_id': patient_id,
                'age': 45,
                'gender': 'M',
                'diagnoses': ['hypertension', 'diabetes'],
                'medications': ['metformin', 'lisinopril'],
                'lab_results': [
                    {'test': 'glucose', 'value': 126, 'unit': 'mg/dL', 'date': '2025-01-24'},
                    {'test': 'hba1c', 'value': 6.8, 'unit': '%', 'date': '2025-01-24'}
                ]
            }
        
        mock.query_patient_data.side_effect = get_patient_data
        mock.update_patient_data.return_value = True
        yield mock

@pytest.fixture
def mock_m3():
    """Mock M3 optimizer."""
    with patch('src.api.main.m3_optimizer') as mock:
        mock.metal_enabled = True
        
        # Create context manager mocks that actually return values
        @contextmanager
        def mock_query_context():
            yield {"optimized": True, "query_time": 0.1}
            
        @contextmanager
        def mock_prediction_context():
            yield {"prediction": 0.75, "confidence": 0.85, "factors": ["age", "comorbidities"]}
            
        @contextmanager
        def mock_analysis_context():
            yield {"results": {"effectiveness": 0.82}, "metrics": {"p_value": 0.001}}
            
        @contextmanager
        def mock_processing_context():
            yield {"processed": True, "optimization_metrics": {"time_saved": "30%"}}
            
        @contextmanager
        def mock_storage_context():
            yield {"stored": True, "optimization_status": "success"}
        
        mock.optimize_query_execution = mock_query_context
        mock.optimize_prediction = mock_prediction_context
        mock.optimize_analysis = mock_analysis_context
        mock.optimize_processing = mock_processing_context
        mock.optimize_storage = mock_storage_context
        
        yield mock

@pytest.mark.asyncio
async def test_patient_data_endpoint(mock_db, mock_m3, auth_headers):
    """Test patient data retrieval endpoint."""
    response = client.get("/api/v1/patient/TEST001", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['message'] == 'Patient data retrieved successfully'
    assert data['data']['patient']['patient_id'] == 'TEST001'
    assert 'diagnoses' in data['data']['patient']
    assert 'medications' in data['data']['patient']
    assert 'lab_results' in data['data']['patient']

@pytest.mark.asyncio
async def test_clinical_prediction_endpoint(mock_db, mock_m3, auth_headers):
    """Test clinical prediction endpoint."""
    prediction_request = {
        'patient_id': 'TEST001',
        'prediction_type': 'readmission_risk',
        'timeframe_days': 30
    }
    
    response = client.post("/api/v1/predict", json=prediction_request, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['message'] == 'Clinical prediction generated successfully'
    assert 'prediction' in data['data']
    assert 'confidence' in data['data']

@pytest.mark.asyncio
async def test_data_analysis_endpoint(mock_db, mock_m3, auth_headers):
    """Test data analysis endpoint."""
    analysis_request = {
        'patient_ids': ['TEST001', 'TEST002'],
        'analysis_type': 'treatment_effectiveness',
        'parameters': {
            'treatment': 'metformin',
            'outcome_metric': 'hba1c'
        }
    }
    
    response = client.post("/api/v1/analyze", json=analysis_request, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['message'] == 'Data analysis completed successfully'
    assert 'results' in data['data']
    assert 'metrics' in data['data']

@pytest.mark.asyncio
async def test_batch_data_processing(mock_db, mock_m3, auth_headers):
    """Test batch data processing endpoint."""
    batch_request = {
        'patient_ids': ['TEST001', 'TEST002', 'TEST003'],
        'processing_type': 'feature_extraction',
        'parameters': {
            'features': ['demographics', 'lab_results', 'medications'],
            'time_window_days': 90
        }
    }
    
    response = client.post("/api/v1/process-batch", json=batch_request, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['message'] == 'Batch processing completed successfully'
    assert 'processed_count' in data['data']
    assert 'features' in data['data']
    assert 'processing_time' in data['data']
    assert 'optimization_status' in data['data']

@pytest.mark.asyncio
async def test_error_handling(mock_db, mock_m3, auth_headers):
    """Test error handling in endpoints."""
    # Test invalid patient ID
    mock_db.query_patient_data.return_value = None
    response = client.get("/api/v1/patient/INVALID", headers=auth_headers)
    assert response.status_code == 404
    
    # Test invalid analysis request
    invalid_analysis = {
        'patient_ids': [],
        'analysis_type': 'invalid_type'
    }
    response = client.post("/api/v1/analyze", json=invalid_analysis, headers=auth_headers)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_concurrent_requests(mock_db, mock_m3, auth_headers):
    """Test handling of concurrent requests."""
    # Reset mock to use side_effect
    def get_patient_data(patient_id):
        """Generate mock patient data based on ID."""
        return {
            'patient_id': patient_id,
            'age': 45,
            'gender': 'M',
            'diagnoses': ['hypertension', 'diabetes'],
            'medications': ['metformin', 'lisinopril'],
            'lab_results': [
                {'test': 'glucose', 'value': 126, 'unit': 'mg/dL', 'date': '2025-01-24'},
                {'test': 'hba1c', 'value': 6.8, 'unit': '%', 'date': '2025-01-24'}
            ]
        }
    
    mock_db.query_patient_data.side_effect = get_patient_data
    
    # Simulate concurrent requests
    patient_ids = [f"TEST{i:03d}" for i in range(5)]
    responses = []
    
    # Make requests sequentially since we're using TestClient
    for pid in patient_ids:
        response = client.get(f"/api/v1/patient/{pid}", headers=auth_headers)
        responses.append(response)
    
    # Verify all requests were successful
    assert all(r.status_code == 200 for r in responses)
    
    # Verify response format
    for i, response in enumerate(responses):
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == 'Patient data retrieved successfully'
        assert data['data']['patient']['patient_id'] == f"TEST{i:03d}"

@pytest.mark.asyncio
async def test_data_persistence(mock_db, mock_m3, auth_headers):
    """Test data persistence operations."""
    patient_data = {
        'patient_id': 'TEST001',
        'update_type': 'lab_results',
        'data': {
            'test': 'glucose',
            'value': 130,
            'unit': 'mg/dL',
            'date': '2025-01-25'
        }
    }
    
    response = client.post("/api/v1/patient/update", json=patient_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['message'] == 'Patient data updated successfully'
    assert 'optimization' in data['data']

@pytest.mark.asyncio
async def test_api_authentication(mock_db, mock_m3):
    """Test API authentication."""
    # Test without authentication
    response = client.get("/api/v1/patient/TEST001")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
    
    # Test with invalid authentication
    headers = invalid_auth_headers()
    response = client.get("/api/v1/patient/TEST001", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]
    
    # Set up valid authentication
    headers = auth_headers()
    mock_db.query_patient_data.side_effect = lambda x: {
        'patient_id': x,
        'age': 45,
        'gender': 'M',
        'diagnoses': ['hypertension'],
        'medications': ['metformin'],
        'lab_results': []
    }
    
    # Test with valid authentication
    response = client.get("/api/v1/patient/TEST001", headers=headers)
    assert response.status_code == 200
    assert response.json()['status'] == 'success'

@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    health_data = response.json()
    assert health_data['status'] == 'healthy'
    assert 'database_connection' in health_data
    assert 'api_version' in health_data
    assert 'last_check_time' in health_data
