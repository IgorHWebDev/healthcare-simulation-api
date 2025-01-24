from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import datetime
import re
import uvicorn

app = FastAPI(
    title="IQHIS API",
    description="Integrated Quantum-Resistant Healthcare Information System API",
    version="0.1.0-sprint.0"
)

# Security
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Current health status")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

class M3Metrics(BaseModel):
    cpu_utilization: float = Field(..., ge=0, le=1)
    memory_usage: float = Field(..., ge=0, le=1)
    gpu_utilization: float = Field(..., ge=0, le=1)

class MetricsResponse(BaseModel):
    encryption_operations: int = Field(..., ge=0)
    key_rotations: int = Field(..., ge=0)
    error_count: int = Field(..., ge=0)
    m3_metrics: M3Metrics

class EncryptionRequest(BaseModel):
    data: str = Field(..., max_length=10485760)  # 10MB limit
    key_id: Optional[str] = Field(None, pattern=r'^qk_\d{4}_\d{2}_\d{2}.*$')

    @field_validator('key_id')
    def validate_key_id(cls, v):
        if v is not None and not re.match(r'^qk_\d{4}_\d{2}_\d{2}.*$', v):
            raise ValueError('Invalid key_id format. Must match pattern: qk_YYYY_MM_DD')
        return v

class EncryptionResponse(BaseModel):
    encrypted_data: str
    key_id: str
    expiry: datetime.datetime

# Routes
@app.get("/v1/quantum/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Get quantum system health status.
    Critical for Sprint 0 environment validation.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.datetime.now()
    )

@app.get("/v1/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def metrics(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Get system metrics with M3 optimization.
    Required for Sprint 0 performance baseline.
    """
    return MetricsResponse(
        encryption_operations=100,
        key_rotations=5,
        error_count=0,
        m3_metrics=M3Metrics(
            cpu_utilization=0.45,
            memory_usage=0.32,
            gpu_utilization=0.28
        )
    )

@app.post("/v1/quantum/encrypt", response_model=EncryptionResponse, tags=["Quantum Security"])
async def encrypt(
    request: EncryptionRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Encrypt data using quantum-resistant encryption.
    Implements CRYSTALS-Kyber1024 encryption with M3 optimization.
    """
    return EncryptionResponse(
        encrypted_data="mock_encrypted_data",
        key_id=request.key_id or f"qk_{datetime.datetime.now().strftime('%Y_%m_%d')}",
        expiry=datetime.datetime.now() + datetime.timedelta(hours=24)
    )

if __name__ == "__main__":
    uvicorn.run(
        "mock_api:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    ) 