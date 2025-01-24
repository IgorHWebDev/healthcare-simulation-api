from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import logging
import uvicorn
from typing import Optional, List
import yaml
import os
import uuid
from pydantic import BaseModel

from models.encryption import (
    EncryptionRequest,
    EncryptionResponse,
    HealthResponse,
    MetricsResponse,
    Error
)
from services.quantum_service import QuantumService
from services.metrics_service import MetricsService
from core.config import Settings
from core.security import validate_token, validate_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("iqhis")

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="Interactive medical scenario simulation and validation API",
    version="1.0.0"
)

# Security schemes
bearer_scheme = HTTPBearer()
api_key_scheme = APIKeyHeader(name="X-API-Key")

# Load settings
settings = Settings()

# Initialize services
quantum_service = QuantumService()
metrics_service = MetricsService()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    message: str

class SimulationResponse(BaseModel):
    scenario_id: str
    response: str
    next_steps: List[str]

class ValidationRequest(BaseModel):
    action: str

class ValidationResponse(BaseModel):
    is_valid: bool
    feedback: str
    score: Optional[float] = None

@app.post("/quantum/encrypt", response_model=EncryptionResponse)
async def encrypt_data(
    request: EncryptionRequest,
    token: str = Depends(bearer_scheme)
) -> EncryptionResponse:
    """
    Encrypt data using quantum-resistant encryption.
    """
    try:
        # Validate JWT token
        if not validate_token(token.credentials):
            raise HTTPException(
                status_code=401,
                detail=Error(
                    code="AUTH_001",
                    message="Invalid or expired JWT token"
                ).dict()
            )

        # Encrypt data using quantum service
        encrypted_data = await quantum_service.encrypt(
            data=request.data,
            key_id=request.key_id
        )

        # Get performance metrics
        perf_metrics = quantum_service.get_performance_metrics()

        return EncryptionResponse(
            encrypted_data=encrypted_data.encrypted_data,
            key_id=encrypted_data.key_id,
            expiry=datetime.utcnow() + timedelta(hours=24),
            performance_metrics=perf_metrics
        )

    except Exception as e:
        logger.error(f"Encryption error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=Error(
                code="QE_001",
                message="Quantum encryption service error",
                details={"error": str(e)}
            ).dict()
        )

@app.get("/quantum/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """
    Get quantum system health status.
    """
    try:
        health_data = await quantum_service.get_health()
        return HealthResponse(
            status=health_data.status,
            last_key_rotation=health_data.last_key_rotation,
            current_load=health_data.current_load,
            quantum_metrics=health_data.quantum_metrics
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=Error(
                code="HEALTH_001",
                message="Health check failed",
                details={"error": str(e)}
            ).dict()
        )

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    api_key: str = Security(api_key_scheme)
) -> MetricsResponse:
    """
    Get system metrics with M3 optimization data.
    """
    try:
        # Validate API key
        if not validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail=Error(
                    code="AUTH_002",
                    message="Invalid API key"
                ).dict()
            )

        metrics_data = await metrics_service.get_metrics()
        return MetricsResponse(
            encryption_operations=metrics_data.encryption_operations,
            key_rotations=metrics_data.key_rotations,
            error_count=metrics_data.error_count,
            m3_metrics=metrics_data.m3_metrics
        )
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=Error(
                code="METRICS_001",
                message="Metrics collection failed",
                details={"error": str(e)}
            ).dict()
        )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/simulate", response_model=SimulationResponse)
async def simulate_scenario(request: SimulationRequest):
    # Simple simulation logic (to be enhanced)
    scenario_id = str(uuid.uuid4())
    
    if "cardiac arrest" in request.message.lower():
        return SimulationResponse(
            scenario_id=scenario_id,
            response="Patient is unconscious, not breathing, no pulse detected.",
            next_steps=[
                "Start chest compressions",
                "Call for AED",
                "Establish airway"
            ]
        )
    
    return SimulationResponse(
        scenario_id=scenario_id,
        response="Starting new medical scenario simulation.",
        next_steps=["Assess patient condition", "Check vital signs"]
    )

@app.post("/validate", response_model=ValidationResponse)
async def validate_action(request: ValidationRequest):
    # Simple validation logic (to be enhanced)
    if "chest compression" in request.action.lower():
        return ValidationResponse(
            is_valid=True,
            feedback="Correct! Starting chest compressions is appropriate for a pulseless patient.",
            score=95.0
        )
    
    return ValidationResponse(
        is_valid=False,
        feedback="Action not recognized. Please follow standard protocols.",
        score=0.0
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 