"""Main application module for Healthcare Simulation API."""

from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKey
from typing import Optional, List, Dict, Union, Any
import logging
import os
import uuid
from pydantic import BaseModel, Field
from enum import Enum
from fastapi.responses import JSONResponse
from .models import (
    PatientStatus, ProtocolType, VitalSigns, Action, Step,
    SimulationRequest, NextStep, SimulationFeedback, CurrentState,
    SimulationResponse, ValidationRequest, ValidationFeedbackStep,
    ProtocolReference, ValidationResponse
)
from datetime import datetime
from .ollama_service import OllamaService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthcare-simulation")

# API Key configuration
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "test_key")  # In production, use a secure key
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Initialize Ollama service
ollama_service = OllamaService()

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=401,
        detail={
            "code": "AUTH_001",
            "message": "Invalid API key"
        }
    )

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="API for healthcare simulation and protocol validation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    error_response = {
        "code": f"ERR_{exc.status_code}",
        "message": str(exc.detail),
        "debug_info": {
            "request_url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
            "timestamp": datetime.now().isoformat()
        }
    }
    logger.error(f"API Error: {error_response}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    return response

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "name": "Healthcare Simulation API",
        "version": "0.1.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/v1/healthcare/simulate", response_model=SimulationResponse)
async def simulate_scenario(
    request: SimulationRequest,
    api_key: str = Depends(get_api_key)
) -> SimulationResponse:
    """
    Process healthcare simulation scenarios.
    """
    try:
        # Create default vital signs
        vital_signs = VitalSigns(**{
            "❤️ דופק": "72",
            "🫁 נשימות": "16",
            "🌡️ חום": "36.5",
            "⚡ לחץ דם": "120/80"
        })

        # Create current state
        current_state = CurrentState(
            patient_status=PatientStatus.UNSTABLE,
            vital_signs=vital_signs,
            current_interventions=[]
        )

        # Create next steps
        next_steps = [
            NextStep(
                action="Assess vital signs",
                protocol_reference="Initial Assessment",
                expected_outcome="Establish baseline patient status"
            )
        ]

        # Create feedback
        feedback = SimulationFeedback(
            correct_actions=["Initial assessment performed"],
            suggestions=["Monitor vital signs", "Prepare emergency equipment"],
            protocol_adherence=85.0
        )

        # Return simulation response
        return SimulationResponse(
            scenario_id=f"sim_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            current_state=current_state,
            next_steps=next_steps,
            feedback=feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/healthcare/validate", response_model=ValidationResponse)
async def validate_protocol(
    request: ValidationRequest,
    api_key: str = Depends(get_api_key)
) -> ValidationResponse:
    """
    Validate healthcare protocols.
    """
    try:
        # Create feedback steps
        feedback = [
            ValidationFeedbackStep(
                step=1,
                action=request.actions[0],
                is_correct=True,
                correction=None
            )
        ]

        # Create references
        references = [
            ProtocolReference(
                protocol=request.protocol_type.value,
                section="Standard Procedures",
                details="Protocol follows standard guidelines"
            )
        ]

        # Return validation response
        return ValidationResponse(
            is_valid=True,
            score=90.0,
            feedback=feedback,
            references=references
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    await ollama_service.close() 