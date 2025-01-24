from fastapi import FastAPI, HTTPException, Security, Depends, APIRouter
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import uuid
from typing import List, Optional, Dict, Any
import logging
from .models import *
from fastapi.responses import JSONResponse
from datetime import datetime
import httpx
import os
import json

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"

# LM Studio configuration
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "medical-model")

async def call_ollama(model: str, prompt: str) -> dict:
    """
    Helper function to call Ollama API with detailed logging
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    request_data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    logger.debug(f"Sending request to Ollama:\nURL: {url}\nData: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=request_data)
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"Received response from Ollama:\n{json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return response_data
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}")
            raise

async def call_lm_studio(prompt: str) -> dict:
    """Call LM Studio local model."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LM_STUDIO_URL}/chat/completions",
                json={
                    "model": LM_STUDIO_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a medical expert providing second opinions."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LM Studio error: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="""Healthcare Simulation API powered by Ollama multi-model support
    Version: Sprint 0 - Development

    Key Features:
    - Advanced healthcare scenario simulation
    - Multi-model support via Ollama
    - Real-time feedback and validation
    - Support for Hebrew language scenarios

    Authentication:
    - Use X-API-Key header for all endpoints except /health
    - For development: use 'test_key'
    - For production: obtain secure key from administrator
    """,
    version="0.1.0",
    contact={
        "name": "Development Team",
        "email": "dev@iqhis.local"
    },
    servers=[
        {"url": "http://localhost:8082", "description": "Local Development Server"},
        {"url": "https://healthcare-simulation-api.onrender.com", "description": "Production API Endpoint"}
    ],
    openapi_tags=[{
        "name": "Healthcare Simulation",
        "description": "Healthcare simulation and training scenarios using Ollama multi-model support"
    }]
)

@app.get("/")
async def root():
    return {"message": "Healthcare Simulation API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Validate API key."""
    if api_key_header == os.getenv("API_KEY", "test_key"):
        return api_key_header
    raise HTTPException(
        status_code=401,
        detail="Invalid API key"
    )

@app.post("/v1/healthcare/simulate", 
         response_model=SimulationResponse,
         tags=["Healthcare Simulation"])
async def simulate_scenario(
    request: SimulationRequest,
    api_key: str = Depends(get_api_key)
) -> SimulationResponse:
    """
    Simulate a healthcare scenario and get LM Studio's second opinion.
    """
    try:
        # Get LM Studio's analysis
        lm_response = await call_lm_studio(
            f"Analyze this medical scenario and provide expert opinion:\n{request.title}\n"
            f"Steps:\n" + "\n".join([f"{s.step}. {s.description}" for s in request.steps])
        )

        # Extract the response
        analysis = lm_response["choices"][0]["message"]["content"]

        # Create response
        return SimulationResponse(
            scenario_id=f"sim_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            current_state=CurrentState(
                patient_status=PatientStatus.UNSTABLE,
                vital_signs=VitalSigns(**{
                    "❤️ דופק": "72",
                    "🫁 נשימות": "16",
                    "🌡️ חום": "36.5",
                    "⚡ לחץ דם": "120/80"
                }),
                current_interventions=[]
            ),
            next_steps=[
                NextStep(
                    action="Analyze LM Studio response",
                    protocol_reference="AI Analysis",
                    expected_outcome=analysis
                )
            ],
            feedback=SimulationFeedback(
                correct_actions=[],
                suggestions=[analysis],
                protocol_adherence=85.0
            )
        )

    except Exception as e:
        logger.error(f"Error processing simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/healthcare/validate",
         response_model=ValidationResponse,
         tags=["Healthcare Simulation"])
async def validate_protocol(
    request: ValidationRequest,
    api_key: str = Depends(get_api_key)
) -> ValidationResponse:
    """
    Validate healthcare protocol with LM Studio's analysis.
    """
    try:
        # Get LM Studio's validation
        lm_response = await call_lm_studio(
            f"Validate this medical protocol:\nType: {request.protocol_type}\n"
            f"Actions:\n" + "\n".join([f"- {action}" for action in request.actions])
        )

        # Extract the validation
        validation = lm_response["choices"][0]["message"]["content"]

        return ValidationResponse(
            is_valid=True,
            score=90.0,
            feedback=[
                ValidationFeedbackStep(
                    step=1,
                    action="LM Studio Analysis",
                    is_correct=True,
                    correction=validation
                )
            ],
            references=[
                ProtocolReference(
                    protocol=request.protocol_type.value,
                    section="AI Analysis",
                    details=validation
                )
            ]
        )

    except Exception as e:
        logger.error(f"Error validating protocol: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    return JSONResponse(status_code=exc.status_code, content=error_response) 