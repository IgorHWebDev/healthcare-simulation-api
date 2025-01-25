from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# PHI Models
class PHIData(BaseModel):
    """Model for Protected Health Information (PHI) data."""
    id: str = Field(..., pattern=r"^PHI_P\d{10}_\d{14}$", description="PHI record identifier")
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    data_type: str = Field(
        ..., 
        pattern=r"^(clinical_note|lab_result|imaging|prescription|demographics)$",
        description="Type of PHI data"
    )
    content: Any = Field(..., description="PHI content")
    encryption_key_id: str = Field(
        ..., 
        pattern=r"^qk_\d{14}(_[a-f0-9]{8})?$",
        description="Encryption key identifier"
    )
    created_at: datetime = Field(..., description="Record creation timestamp")

class PHIRequest(BaseModel):
    """Model for PHI storage request."""
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    data_type: str = Field(
        ..., 
        pattern=r"^(clinical_note|lab_result|imaging|prescription|demographics)$",
        description="Type of PHI data"
    )
    content: Any = Field(..., description="PHI content to store")

class PHIResponse(BaseModel):
    """Model for PHI operation response."""
    id: str = Field(..., pattern=r"^PHI_P\d{10}_\d{14}$", description="PHI record identifier")
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    data_type: str = Field(
        ..., 
        pattern=r"^(clinical_note|lab_result|imaging|prescription|demographics)$",
        description="Type of PHI data"
    )
    content: Any = Field(..., description="PHI content")
    encryption_key_id: str = Field(
        ..., 
        pattern=r"^qk_\d{14}(_[a-f0-9]{8})?$",
        description="Encryption key identifier"
    )
    created_at: datetime = Field(..., description="Record creation timestamp")

class PHIQuery(BaseModel):
    """Model for PHI retrieval query."""
    patient_id: Optional[str] = Field(None, pattern=r"^P\d{10}$", description="Patient identifier")
    start_date: Optional[datetime] = Field(None, description="Query start date")
    end_date: Optional[datetime] = Field(None, description="Query end date")

class AuditLogEntry(BaseModel):
    """Model for audit log entry."""
    user_id: str = Field(..., description="User identifier")
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    action: str = Field(..., pattern=r"^(read|write|delete)$", description="Action performed")
    resource_type: str = Field(..., pattern=r"^(phi|audit|metrics)$", description="Resource type")
    resource_id: str = Field(..., description="Resource identifier")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")

class EncryptionRequest(BaseModel):
    """
    Request model for encryption endpoint
    """
    data: str = Field(..., description="Data to encrypt")
    key_id: Optional[str] = Field(
        None,
        pattern=r"^qk_\d{14}(_[a-f0-9]{8})?$",
        description="Optional key ID for encryption"
    )

class EncryptionResponse(BaseModel):
    """
    Model for encryption response.
    """
    encrypted_data: str
    key_id: str = Field(
        ...,
        pattern=r"^qk_\d{14}(_[a-f0-9]{8})?$",
        description="Key ID used for encryption"
    )
    expiry: datetime

class HealthResponse(BaseModel):
    """
    Model for health check response.
    """
    status: str = Field(..., pattern=r"^(healthy|unhealthy)$")
    timestamp: datetime

class MetricsResponse(BaseModel):
    """
    Model for metrics response.
    """
    requests_total: int
    errors_total: int
    latency_ms: float

class AuditQuery(BaseModel):
    """Model for audit log query."""
    patient_id: Optional[str] = Field(None, pattern=r"^P\d{10}$", description="Patient identifier")
    start_date: Optional[datetime] = Field(None, description="Query start date")
    end_date: Optional[datetime] = Field(None, description="Query end date")
    action: Optional[str] = Field(
        None, 
        pattern=r"^(read|write|delete)$",
        description="Action to filter by"
    )

# DICOM Models
class DICOMData(BaseModel):
    """Model for DICOM data."""
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    study_uid: str = Field(..., description="Study instance UID")
    series_uid: str = Field(..., description="Series instance UID")
    image_data: bytes = Field(..., description="DICOM image data")
    metadata: Dict[str, Any] = Field(..., description="DICOM metadata")

class DICOMResponse(BaseModel):
    """Model for DICOM operation response."""
    image_id: str = Field(..., description="Image identifier")
    study_uid: str = Field(..., description="Study instance UID")
    series_uid: str = Field(..., description="Series instance UID")
    status: str = Field(..., pattern=r"^(success|error)$", description="Operation status")

class DICOMQuery(BaseModel):
    """Model for DICOM retrieval query."""
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    study_uid: Optional[str] = Field(None, description="Study instance UID")
    series_uid: Optional[str] = Field(None, description="Series instance UID")
    image_id: Optional[str] = Field(None, description="Image identifier")

class MetadataQuery(BaseModel):
    """Model for DICOM metadata query."""
    image_id: str = Field(..., description="Image identifier")
    include_private_tags: bool = Field(False, description="Whether to include private DICOM tags")

# FHIR Models
class PatientResource(BaseModel):
    """Model for FHIR Patient resource."""
    identifier: List[Dict[str, str]] = Field(..., description="Patient identifiers")
    active: bool = Field(..., description="Whether the patient record is active")
    name: List[Dict[str, str]] = Field(..., description="Patient names")
    telecom: Optional[List[Dict[str, str]]] = Field(None, description="Patient contact details")
    gender: str = Field(
        ..., 
        pattern=r"^(male|female|other|unknown)$",
        description="Patient gender"
    )
    birthDate: str = Field(..., description="Patient birth date")
    address: Optional[List[Dict[str, str]]] = Field(None, description="Patient addresses")

class ObservationResource(BaseModel):
    """Model for FHIR Observation resource."""
    identifier: List[Dict[str, str]] = Field(..., description="Observation identifiers")
    status: str = Field(
        ..., 
        pattern=r"^(registered|preliminary|final|amended)$",
        description="Observation status"
    )
    category: List[Dict[str, str]] = Field(..., description="Observation category")
    code: Dict[str, Any] = Field(..., description="Observation code")
    subject: Dict[str, str] = Field(..., description="Subject of observation")
    effectiveDateTime: str = Field(..., description="Time of observation")
    value: Dict[str, Any] = Field(..., description="Observation value")

class DiagnosticReport(BaseModel):
    """Model for FHIR DiagnosticReport resource."""
    identifier: List[Dict[str, str]] = Field(..., description="Report identifiers")
    status: str = Field(..., description="Report status")
    category: Dict[str, Any] = Field(..., description="Report category")
    code: Dict[str, Any] = Field(..., description="Report code")
    subject: Dict[str, str] = Field(..., description="Subject of report")
    effectiveDateTime: str = Field(..., description="Time of report")
    issued: str = Field(..., description="Report issue time")
    performer: List[Dict[str, str]] = Field(..., description="Report performers")
    result: List[Dict[str, str]] = Field(..., description="Report results")

# Common Models
class ErrorResponse(BaseModel):
    """Model for error responses."""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

class QueryRequest(BaseModel):
    """Request model for healthcare queries."""
    query: str = Field(..., min_length=1, description="The healthcare query to process")
    model: str = Field("mistral", description="The AI model to use")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Temperature for response generation")

class ProtocolRequest(BaseModel):
    """Request model for protocol validation."""
    protocol: str = Field(..., min_length=1, description="The healthcare protocol to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Protocol parameters")
    guidelines: Optional[Dict[str, Any]] = Field(None, description="Optional guidelines for validation")

class AnalysisRequest(BaseModel):
    """Request model for medical data analysis."""
    data: Dict[str, Any] = Field(..., description="Medical data to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional analysis parameters")

class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    analysis: str = Field(..., description="Analysis results")
    timestamp: datetime = Field(..., description="Timestamp of the analysis")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    recommendations: List[str] = Field(..., description="List of recommendations")

class ValidationResponse(BaseModel):
    """Response model for protocol validation."""
    is_valid: bool = Field(..., description="Whether the protocol is valid")
    validation_details: str = Field(..., description="Details of the validation")
    timestamp: datetime = Field(..., description="Timestamp of the validation") 