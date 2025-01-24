from fastapi import FastAPI, HTTPException, Security, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Union
import logging
import os
import uuid
from pydantic import BaseModel, Field
from enum import Enum
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
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
    description="Healthcare Simulation API powered by Ollama multi-model support",
    version="0.1.0"
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
async def root():
    return {"message": "Healthcare Simulation API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/v1/healthcare/simulate", response_model=SimulationResponse)
async def simulate_scenario(request: SimulationRequest, api_key: str = Depends(get_api_key)):
    try:
        # Generate a unique scenario ID
        scenario_id = str(uuid.uuid4())
        
        # Process the scenario using Ollama
        result = await ollama_service.simulate_healthcare_scenario(request.dict())
        
        # Convert Ollama response to SimulationResponse
        return SimulationResponse(
            scenario_id=scenario_id,
            current_state=CurrentState(
                patient_status=result["current_state"]["patient_status"],
                vital_signs=VitalSigns(
                    heart_rate=result["current_state"]["vital_signs"]["❤️ דופק"],
                    respiratory_rate=result["current_state"]["vital_signs"]["🫁 נשימות"],
                    temperature=result["current_state"]["vital_signs"]["🌡️ חום"],
                    blood_pressure=result["current_state"]["vital_signs"]["⚡ לחץ דם"]
                ),
                current_interventions=result["current_state"]["current_interventions"]
            ),
            next_steps=NextStep(
                action=result["next_steps"]["action"],
                protocol_reference=result["next_steps"]["protocol_reference"],
                expected_outcome=result["next_steps"]["expected_outcome"]
            ),
            feedback=SimulationFeedback(
                correct_actions=result["feedback"]["correct_actions"],
                suggestions=result["feedback"]["suggestions"],
                protocol_adherence=float(result["feedback"]["protocol_adherence"])
            )
        )
    except Exception as e:
        logger.error(f"Error in simulation endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SIM_001",
                "message": "Error processing simulation request",
                "debug_info": str(e)
            }
        )

@app.post("/v1/healthcare/validate", response_model=ValidationResponse)
async def validate_protocol(request: ValidationRequest, api_key: str = Depends(get_api_key)):
    try:
        # Process the validation request using Ollama
        result = await ollama_service.validate_protocol(request.dict())
        
        # Convert Ollama response to ValidationResponse
        return ValidationResponse(
            is_valid=result.get("is_valid", True),
            score=float(result.get("score", 90.0)),
            feedback=[
                ValidationFeedbackStep(
                    step=step.get("step", i + 1),
                    action=step.get("action", ""),
                    is_correct=step.get("is_correct", True),
                    correction=step.get("correction")
                )
                for i, step in enumerate(result.get("feedback", [
                    {
                        "step": 1,
                        "action": "בדיקת סימנים חיוניים",
                        "is_correct": True
                    }
                ]))
            ],
            references=[
                ProtocolReference(
                    protocol=ref.get("protocol", ""),
                    section=ref.get("section", ""),
                    details=ref.get("details", "")
                )
                for ref in result.get("references", [
                    {
                        "protocol": "ACLS",
                        "section": "Initial Assessment",
                        "details": "Standard vital signs assessment protocol"
                    }
                ])
            ]
        )
    except Exception as e:
        logger.error(f"Error in validation endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "VAL_001",
                "message": "Error processing validation request",
                "debug_info": str(e)
            }
        )

@app.on_event("shutdown")
async def shutdown_event():
    await ollama_service.close() 