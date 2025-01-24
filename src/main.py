from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
import uvicorn
import os
import uuid
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthcare-simulation")

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="Interactive medical scenario simulation and validation API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/simulate", response_model=SimulationResponse)
async def simulate_scenario(request: SimulationRequest):
    # Simple simulation logic
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
    # Simple validation logic
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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 