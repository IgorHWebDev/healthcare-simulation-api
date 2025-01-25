"""
Tests for MIMIC-4 Database Adapter.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from src.database.mimic4_adapter import MIMIC4Adapter
from src.database.schema.mimic4_schema import Patient, Admission, ICUStay
from src.utils.m3_optimization import M3Optimizer

@pytest.fixture
async def mimic4_adapter():
    """Create test MIMIC4Adapter instance."""
    config = {
        "connection_string": "sqlite:///test_mimic4.db",
        "demo_mode": True
    }
    adapter = MIMIC4Adapter(config)
    await adapter.connect()
    return adapter

@pytest.mark.asyncio
async def test_connect(mimic4_adapter):
    """Test database connection."""
    assert mimic4_adapter.connection is not None
    assert await mimic4_adapter.connect() is True

@pytest.mark.asyncio
async def test_query_patient(mimic4_adapter):
    """Test patient query."""
    # Test with demo patient ID
    patient_data = await mimic4_adapter.query(
        "SELECT * FROM patients WHERE subject_id = :id",
        {"id": 10006}
    )
    assert len(patient_data) > 0
    assert patient_data[0]["subject_id"] == 10006

@pytest.mark.asyncio
async def test_process_patient_data(mimic4_adapter):
    """Test comprehensive patient data processing."""
    patient_data = await mimic4_adapter.process_patient_data(10006)
    assert "patient" in patient_data
    assert "admissions" in patient_data
    assert "lab_results" in patient_data
    assert patient_data["patient"]["subject_id"] == 10006

@pytest.mark.asyncio
async def test_get_vital_signs(mimic4_adapter):
    """Test vital signs retrieval."""
    timeframe = {
        "start": datetime.now() - timedelta(days=30),
        "end": datetime.now()
    }
    vitals = await mimic4_adapter.get_vital_signs(10006, timeframe)
    assert isinstance(vitals, list)
    if len(vitals) > 0:
        assert "charttime" in vitals[0]
        assert "valuenum" in vitals[0]

@pytest.mark.asyncio
async def test_store_patient(mimic4_adapter):
    """Test patient data storage."""
    test_patient = {
        "subject_id": 99999,
        "gender": "F",
        "anchor_age": 45,
        "anchor_year": 2020
    }
    success = await mimic4_adapter.store("patients", test_patient)
    assert success is True
    
    # Verify storage
    stored_patient = await mimic4_adapter.query(
        "SELECT * FROM patients WHERE subject_id = :id",
        {"id": 99999}
    )
    assert len(stored_patient) == 1
    assert stored_patient[0]["subject_id"] == 99999

@pytest.mark.asyncio
async def test_validate_schema(mimic4_adapter):
    """Test schema validation."""
    assert mimic4_adapter.validate_schema("patients") is True
    assert mimic4_adapter.validate_schema("admissions") is True
    assert mimic4_adapter.validate_schema("icustays") is True

@pytest.mark.asyncio
async def test_m3_optimization(mimic4_adapter):
    """Test M3 optimization features."""
    with mimic4_adapter.m3_optimizer.optimize_query_execution():
        result = await mimic4_adapter.query(
            "SELECT * FROM patients LIMIT 10"
        )
    assert isinstance(result, list)
    assert len(result) == 10

@pytest.mark.asyncio
async def test_error_handling(mimic4_adapter):
    """Test error handling."""
    # Test invalid query
    with pytest.raises(Exception):
        await mimic4_adapter.query("SELECT * FROM nonexistent_table")
    
    # Test invalid patient ID
    patient_data = await mimic4_adapter.process_patient_data(-1)
    assert patient_data == {} or patient_data is None

@pytest.mark.asyncio
async def test_concurrent_queries(mimic4_adapter):
    """Test concurrent query execution."""
    async def query_patient(subject_id: int):
        return await mimic4_adapter.query(
            "SELECT * FROM patients WHERE subject_id = :id",
            {"id": subject_id}
        )
    
    # Execute multiple queries concurrently
    patient_ids = [10006, 10008, 10010]
    tasks = [query_patient(pid) for pid in patient_ids]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    for result in results:
        assert len(result) > 0

@pytest.mark.asyncio
async def test_data_encryption(mimic4_adapter):
    """Test data encryption features."""
    test_data = {
        "subject_id": 88888,
        "sensitive_data": "test_value"
    }
    
    # Store encrypted data
    encrypted_data = mimic4_adapter.encryption.encrypt_data(test_data)
    success = await mimic4_adapter.store("test_encryption", encrypted_data)
    assert success is True
    
    # Retrieve and decrypt
    retrieved_data = await mimic4_adapter.query(
        "SELECT * FROM test_encryption WHERE subject_id = :id",
        {"id": 88888}
    )
    decrypted_data = mimic4_adapter.encryption.decrypt_data(retrieved_data[0])
    assert decrypted_data["sensitive_data"] == "test_value"
