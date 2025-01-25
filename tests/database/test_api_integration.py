"""
Tests for Healthcare API Integration.
"""
import pytest
from datetime import datetime
from typing import Dict, List

from src.api.healthcare_api_integration import HealthcareAPIIntegration
from src.api.clinical_decision_support import ClinicalDecisionSupport

@pytest.fixture
async def api_integration():
    """Create test HealthcareAPIIntegration instance."""
    config = {
        "api_token": "test_token",
        "terminology_service_url": "http://test.terminology.com",
        "guidelines_service_url": "http://test.guidelines.com",
        "mimic4": {
            "connection_string": "sqlite:///test_mimic4.db",
            "demo_mode": True
        }
    }
    return HealthcareAPIIntegration(config)

@pytest.fixture
async def cds_system(api_integration):
    """Create test ClinicalDecisionSupport instance."""
    config = {
        "api": api_integration.config
    }
    return ClinicalDecisionSupport(config)

@pytest.mark.asyncio
async def test_fhir_transformation(api_integration):
    """Test FHIR data transformation."""
    patient_fhir = await api_integration.get_patient_fhir(10006)
    assert patient_fhir["resourceType"] == "Bundle"
    assert "entry" in patient_fhir
    
    # Verify patient resource
    patient = patient_fhir["entry"][0]["resource"]
    assert patient["resourceType"] == "Patient"
    assert "id" in patient
    assert "gender" in patient

@pytest.mark.asyncio
async def test_smart_on_fhir_submission(api_integration):
    """Test SMART on FHIR data submission."""
    test_data = {
        "resourceType": "Observation",
        "id": "test-obs-1",
        "status": "final",
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate"
            }]
        }
    }
    
    success = await api_integration.submit_to_smart_on_fhir(
        test_data,
        "http://test.smart.com/fhir/Observation"
    )
    assert success is True

@pytest.mark.asyncio
async def test_terminology_service(api_integration):
    """Test terminology service integration."""
    result = await api_integration.query_terminology_service(
        "8867-4",
        "http://loinc.org"
    )
    assert result is not None
    if result:
        assert "code" in result
        assert "display" in result

@pytest.mark.asyncio
async def test_clinical_guidelines(api_integration):
    """Test clinical guidelines retrieval."""
    guidelines = await api_integration.get_clinical_guidelines("J45.909")  # Asthma
    assert guidelines is not None
    if guidelines:
        assert "recommendations" in guidelines
        assert len(guidelines["recommendations"]) > 0

@pytest.mark.asyncio
async def test_treatment_recommendations(cds_system):
    """Test treatment recommendations generation."""
    recommendations = await cds_system.get_treatment_recommendations(
        10006,
        "J45.909"  # Asthma
    )
    assert recommendations is not None
    if recommendations:
        assert "recommendations" in recommendations
        assert "patient_factors" in recommendations

@pytest.mark.asyncio
async def test_drug_interactions(cds_system):
    """Test drug interaction analysis."""
    test_medications = [
        {"code": "1049502", "name": "Warfarin"},
        {"code": "1049589", "name": "Aspirin"}
    ]
    
    interactions = await cds_system.analyze_drug_interactions(test_medications)
    assert interactions is not None
    assert "interactions_found" in interactions
    assert "severity_level" in interactions

@pytest.mark.asyncio
async def test_lab_trends(cds_system):
    """Test laboratory trend analysis."""
    lab_codes = ["8867-4", "8462-4"]  # Heart rate, Blood pressure
    trends = await cds_system.evaluate_lab_trends(10006, lab_codes)
    
    assert trends is not None
    assert "trends" in trends
    assert "reference_ranges" in trends
    assert "alerts" in trends

@pytest.mark.asyncio
async def test_outcome_prediction(cds_system):
    """Test outcome prediction."""
    predictions = await cds_system.predict_outcomes(10006, "J45.909")
    
    assert predictions is not None
    assert "mortality_risk" in predictions
    assert "readmission_risk" in predictions
    assert "los_prediction" in predictions
    
    # Verify prediction ranges
    assert 0 <= predictions["mortality_risk"] <= 1
    assert 0 <= predictions["readmission_risk"] <= 1
    assert predictions["los_prediction"] >= 0

@pytest.mark.asyncio
async def test_error_handling(api_integration, cds_system):
    """Test error handling in API integration."""
    # Test invalid patient ID
    invalid_fhir = await api_integration.get_patient_fhir(-1)
    assert invalid_fhir == {}
    
    # Test invalid condition code
    invalid_recommendations = await cds_system.get_treatment_recommendations(
        10006,
        "INVALID_CODE"
    )
    assert invalid_recommendations == {}
