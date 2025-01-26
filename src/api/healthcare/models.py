"""
Healthcare data models for the API.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class PatientStatusEnum(str, Enum):
    """Patient status in Hebrew."""
    STABLE = "יציב"
    UNSTABLE = "לא יציב"
    CRITICAL = "קריטי"

class ProtocolType(str, Enum):
    """Type of medical protocol."""
    ACLS = "ACLS"
    BLS = "BLS"
    PALS = "PALS"
    TRAUMA = "TRAUMA"

class MeasurementValue(BaseModel):
    """Model for measurement values with units."""
    value: float
    unit: str

class BloodPressure(BaseModel):
    """Model for blood pressure measurements."""
    systolic: MeasurementValue
    diastolic: MeasurementValue

class VitalSigns(BaseModel):
    """Model for vital signs measurements."""
    heart_rate: MeasurementValue
    blood_pressure: BloodPressure
    respiratory_rate: MeasurementValue
    temperature: MeasurementValue
    oxygen_saturation: MeasurementValue

class PatientData(BaseModel):
    """Model for patient data."""
    age: Optional[int] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    vital_signs: Optional[VitalSigns] = None

class Action(BaseModel):
    """Model for simulation action."""
    action: str = Field(..., description="Action to be taken")
    details: str = Field(..., description="Detailed description of the action")
    references: Optional[List[str]] = Field(default_factory=list, description="Reference materials")

class Step(BaseModel):
    """Model for simulation step."""
    step: int = Field(..., description="Step number")
    description: str = Field(..., description="Step description")
    actions: List[Action] = Field(..., description="Actions to be taken")

class SimulationRequest(BaseModel):
    """Model for simulation request."""
    scenario: str = Field(..., description="Healthcare scenario to simulate")
    title: str = Field(..., description="Title of the simulation scenario")
    actors: List[str] = Field(..., description="List of actors involved in the scenario")
    steps: List[Step] = Field(..., description="List of steps in the scenario")
    patient_data: Optional[PatientData] = None

class SimulationResponse(BaseModel):
    """Model for simulation response."""
    diagnosis: str = Field(..., description="Preliminary diagnosis based on scenario")
    recommended_actions: List[str] = Field(..., description="List of recommended actions")
    vital_signs: Dict[str, Any] = Field(..., description="Current vital signs with trends")
    risk_assessment: str = Field(..., description="Risk assessment based on scenario")
    next_steps: List[str] = Field(..., description="Recommended next steps")

class ValidationRequest(BaseModel):
    """Model for validation request."""
    protocol: str = Field(..., description="Healthcare protocol to validate")
    protocol_type: str = Field(..., description="Type of protocol (e.g., ACLS, BLS)")
    steps: List[str] = Field(..., description="Steps in the protocol")
    actions: List[str] = Field(..., description="Actions to be taken")

class ValidationResponse(BaseModel):
    """Model for validation response."""
    is_valid: bool = Field(..., description="Whether the protocol is valid")
    score: float = Field(..., description="Validation score (0-100)", ge=0, le=100)
    feedback: List[str] = Field(..., description="Feedback on protocol steps")
    references: List[str] = Field(..., description="Relevant medical references")

class Error(BaseModel):
    """Model for error responses."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")

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
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class PatientStatus(BaseModel):
    """Model for patient status information."""
    status_type: PatientStatusEnum = Field(..., description="Current status of the patient")
    vital_signs: Dict[str, float] = Field(..., description="Current vital signs")
    last_update: str = Field(..., description="Timestamp of the last status update")
    notes: Optional[str] = Field(None, description="Additional notes about patient status")
    risk_level: Optional[int] = Field(None, ge=0, le=10, description="Risk level from 0-10")
    monitoring_required: bool = Field(default=False, description="Whether continuous monitoring is required")

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
