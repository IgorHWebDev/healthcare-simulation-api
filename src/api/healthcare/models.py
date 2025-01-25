"""
Healthcare data models for the API.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class LabResult(BaseModel):
    """Lab result data model."""
    test: str
    value: float
    unit: str
    date: str

class PatientData(BaseModel):
    """Patient data model."""
    patient_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnoses: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    lab_results: Optional[List[LabResult]] = None

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
