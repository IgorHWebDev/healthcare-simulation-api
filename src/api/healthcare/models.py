"""
Healthcare data models for the API.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from uuid import UUID

class VitalSigns(BaseModel):
    blood_pressure: str
    heart_rate: int
    temperature: float
    respiratory_rate: int
    oxygen_saturation: int

class LabResult(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    test_date: str

class Diagnosis(BaseModel):
    icd_code: str
    description: Optional[str] = None

class Medication(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class PatientData(BaseModel):
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: str
    age: int
    gender: str
    conditions: List[Diagnosis]
    medications: List[Medication]
    vital_signs: VitalSigns
    lab_results: List[LabResult]

class PatientCreateRequest(BaseModel):
    patient_data: PatientData

class ClinicalPrediction(BaseModel):
    """Clinical prediction request model."""
    patient_id: str
    prediction_type: str
    timeframe_days: Optional[int] = 30
    parameters: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    """Analysis request model."""
    patient_ids: List[str]
    analysis_type: str
    parameters: Optional[Dict[str, Any]] = None

class HealthcareResponse(BaseModel):
    """Standard API response model."""
    status: str = Field(default="success")
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

class BatchRequest(BaseModel):
    """Batch processing request model."""
    patient_ids: List[str]
    processing_type: str
    parameters: Optional[Dict[str, Any]] = None

class UpdateRequest(BaseModel):
    """Patient data update request model."""
    patient_id: str
    update_type: str
    data: Dict[str, Any]
