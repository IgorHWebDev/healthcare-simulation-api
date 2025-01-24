from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class EncryptionRequest(BaseModel):
    message: str = Field(..., description="Message to be encrypted")
    key_id: Optional[str] = Field(
        None,
        description="Optional key ID in format qk_YYYY_MM_DD",
        pattern=r"^qk_\d{4}_\d{2}_\d{2}.*$"
    )
    
    @field_validator('key_id')
    def validate_key_id(cls, v):
        if v is not None and not re.match(r"^qk_\d{4}_\d{2}_\d{2}.*$", v):
            raise ValueError("Invalid key_id format")
        return v

class EncryptionResponse(BaseModel):
    encrypted_message: str
    key_id: str
    signature: str

class HealthResponse(BaseModel):
    status: str = "ok"

class MetricsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float

class Error(BaseModel):
    detail: str 