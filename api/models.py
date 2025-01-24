from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator

class EncryptionRequest(BaseModel):
    """Request model for encryption."""
    data: str = Field(..., description="Data to be encrypted (supports PHI with HIPAA compliance)", max_length=10485760)
    key_id: Optional[str] = Field(
        None,
        pattern=r"^qk_\d{4}_\d{2}_\d{2}.*$",
        description="Optional key ID for encryption"
    )

class EncryptionResponse(BaseModel):
    """Response model for encryption."""
    encrypted_data: str = Field(..., description="Quantum-resistant encrypted data")
    key_id: str = Field(..., description="Key ID used for encryption")
    expiry: datetime = Field(..., description="Expiration time of the encrypted data")
    performance_metrics: Optional[Dict[str, float]] = Field(
        None,
        description="M3 optimization metrics"
    )

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Current health status", pattern=r"^(healthy|degraded|unhealthy)$")
    last_key_rotation: datetime = Field(..., description="Timestamp of last key rotation")
    current_load: float = Field(..., description="Current system load (0-1)", ge=0.0, le=1.0)
    quantum_metrics: Optional[Dict[str, Any]] = Field(None, description="Quantum system metrics")

class MetricsResponse(BaseModel):
    """Response model for metrics."""
    encryption_operations: int = Field(..., description="Total number of encryption operations")
    key_rotations: int = Field(..., description="Total number of key rotations")
    error_count: int = Field(..., description="Total number of errors")
    m3_metrics: Optional[Dict[str, float]] = Field(
        None,
        description="M3 optimization metrics including CPU, memory, and GPU utilization"
    )

class Error(BaseModel):
    """Model for error responses."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Healthcare specific models below
class HealthcareQuery(BaseModel):
    """Model for healthcare query requests."""
    query: str = Field(..., min_length=1, description="The healthcare query to process")
    model: str = Field("mistral", description="The AI model to use")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Temperature for response generation")

class AnalysisResponse(BaseModel):
    """Model for healthcare query responses."""
    analysis: str = Field(..., description="Analysis results")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    recommendations: List[str] = Field(..., description="List of recommendations")
    timestamp: datetime = Field(..., description="Timestamp of the analysis")

class ValidationRequest(BaseModel):
    """Model for protocol validation requests."""
    protocol: str = Field(..., min_length=1, description="Protocol to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Protocol parameters")

class ValidationResponse(BaseModel):
    """Model for protocol validation responses."""
    is_valid: bool = Field(..., description="Whether the protocol is valid")
    issues: List[str] = Field(default_factory=list, description="List of validation issues")
    suggestions: List[str] = Field(default_factory=list, description="List of improvement suggestions")

class PHIRequest(BaseModel):
    """Request model for storing PHI data."""
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    data_type: str = Field(..., pattern=r"^(clinical_note|lab_result|imaging|prescription|demographics)$")
    content: Dict[str, Any] = Field(..., description="PHI content to store")

class PHIResponse(BaseModel):
    """Response model for PHI data."""
    id: str = Field(..., pattern=r"^PHI_P\d{10}_\d{14}$", description="PHI record identifier")
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    data_type: str = Field(..., pattern=r"^(clinical_note|lab_result|imaging|prescription|demographics)$")
    content: Dict[str, Any] = Field(..., description="PHI content")
    encryption_key_id: str = Field(..., pattern=r"^qk_\d{14}(_[a-f0-9]{8})?$")
    created_at: datetime = Field(..., description="Record creation timestamp")

class PHIData(BaseModel):
    """Internal model for PHI data."""
    id: str
    patient_id: str
    data_type: str
    content: Dict[str, Any]
    created_at: datetime
    encryption_key_id: str

class AuditLogEntry(BaseModel):
    """Model for audit log entries."""
    timestamp: datetime = Field(..., description="Event timestamp")
    user_id: str = Field(..., description="User identifier")
    patient_id: str = Field(..., pattern=r"^P\d{10}$", description="Patient identifier")
    action: str = Field(..., pattern=r"^(read|write|delete)$", description="Action performed")
    resource_type: str = Field(..., pattern=r"^(phi|audit|metrics)$", description="Resource type")
    resource_id: str = Field(..., description="Resource identifier")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional event details")

class AuditLogResponse(BaseModel):
    """Response model for audit logs."""
    logs: List[AuditLogEntry] = Field(..., description="List of audit log entries") 