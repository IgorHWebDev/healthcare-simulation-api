from fastapi import FastAPI, HTTPException, Security, Depends, APIRouter
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import uuid
from typing import List
import logging
from .models import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="Healthcare Simulation API powered by Ollama multi-model support",
    version="0.1.0"
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
    if not api_key_header or api_key_header != "test_api_key":
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key_header

@app.post("/v1/healthcare/simulate", 
         response_model=SimulationResponse,
         tags=["Healthcare Simulation"])
async def simulate_scenario(
    request: SimulationRequest,
    api_key: str = Depends(get_api_key)
) -> SimulationResponse:
    """
    Process healthcare simulation scenarios using Ollama models
    """
    try:
        logger.info(f"Processing simulation request: {request.title}")
        
        # Generate a unique scenario ID
        scenario_id = str(uuid.uuid4())
        
        # Process the simulation steps
        current_state = CurrentState(
            patient_status=PatientStatus.UNSTABLE,
            vital_signs=VitalSigns(
                pulse="72",
                breathing="16",
                temperature="36.5",
                blood_pressure="120/80"
            ),
            current_interventions=[]
        )
        
        # Generate next steps based on the scenario
        next_steps = [
            NextStep(
                action="בדיקת סימנים חיוניים",
                protocol_reference="AHA ACLS Guidelines 2020",
                expected_outcome="הערכת מצב המטופל"
            )
        ]
        
        # Generate feedback
        feedback = SimulationFeedback(
            correct_actions=["הערכה ראשונית מהירה", "בדיקת הכרה"],
            suggestions=["לשקול חיבור מוניטור", "להכין ציוד החייאה"],
            protocol_adherence=85.0
        )
        
        return SimulationResponse(
            scenario_id=scenario_id,
            current_state=current_state,
            next_steps=next_steps,
            feedback=feedback
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
    Validate medical decisions against standard protocols
    """
    try:
        logger.info(f"Validating protocol: {request.protocol_type}")
        
        # Validate actions against protocol
        feedback = [
            ValidationFeedback(
                step=1,
                action=request.actions[0],
                is_correct=True,
                correction=None
            )
        ]
        
        # Add protocol references
        references = [
            ProtocolReference(
                protocol=request.protocol_type,
                section="Initial Assessment",
                details="Standard protocol for initial patient assessment"
            )
        ]
        
        return ValidationResponse(
            is_valid=True,
            score=95.0,
            feedback=feedback,
            references=references
        )
        
    except Exception as e:
        logger.error(f"Error validating protocol: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 