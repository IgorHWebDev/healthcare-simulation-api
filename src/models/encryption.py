from pydantic import BaseModel, Field, constr
from typing import Optional, Dict
from datetime import datetime

class EncryptionRequest(BaseModel):
    data: constr(max_length=10485760) = Field(
        ...,
        description="Data to be encrypted (supports PHI with HIPAA compliance)"
    )
    key_id: Optional[constr(regex=r"^qk_\d{4}_\d{2}_\d{2}.*$")] = Field(
        None,
        description="Optional key ID for encryption"
    )

class PerformanceMetrics(BaseModel):
    encryption_time_ms: float = Field(..., description="Encryption time in milliseconds")
    m3_acceleration_factor: float = Field(..., description="M3 acceleration factor achieved")

class EncryptionResponse(BaseModel):
    encrypted_data: str = Field(..., description="Quantum-resistant encrypted data")
    key_id: str = Field(..., description="Key ID used for encryption")
    expiry: datetime = Field(..., description="Expiration time of the encrypted data")
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="M3 optimization metrics")

class QuantumMetrics(BaseModel):
    key_strength: str = Field(
        ...,
        description="Current key strength status",
        regex="^(optimal|acceptable|needs_rotation)$"
    )
    encryption_queue_size: int = Field(..., description="Current encryption queue size")
    active_sessions: int = Field(..., description="Number of active encryption sessions")

class HealthResponse(BaseModel):
    status: str = Field(
        ...,
        description="Current health status",
        regex="^(healthy|degraded|unhealthy)$"
    )
    last_key_rotation: datetime = Field(..., description="Timestamp of last key rotation")
    current_load: float = Field(
        ...,
        description="Current system load (0-1)",
        ge=0.0,
        le=1.0
    )
    quantum_metrics: Optional[QuantumMetrics] = Field(None, description="Quantum system metrics")

class M3Metrics(BaseModel):
    cpu_utilization: float = Field(..., description="CPU utilization percentage", ge=0.0, le=100.0)
    memory_usage: float = Field(..., description="Memory usage percentage", ge=0.0, le=100.0)
    gpu_utilization: float = Field(..., description="GPU utilization percentage", ge=0.0, le=100.0)

class MetricsResponse(BaseModel):
    encryption_operations: int = Field(..., description="Total number of encryption operations")
    key_rotations: int = Field(..., description="Total number of key rotations")
    error_count: int = Field(..., description="Total number of errors")
    m3_metrics: Optional[M3Metrics] = Field(None, description="M3 optimization metrics")

class Error(BaseModel):
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict] = Field(None, description="Additional error details") 