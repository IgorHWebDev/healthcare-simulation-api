from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Union
import logging
import uvicorn
import os
import uuid
from pydantic import BaseModel, Field
from enum import Enum
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthcare-simulation")

# API Key configuration
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "test_key")  # In production, use a secure key
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

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
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "code": f"SRV_{exc.status_code}",
            "message": str(exc.detail)
        }
    )

class PatientStatus(str, Enum):
    STABLE = "יציב"
    UNSTABLE = "לא יציב"
    CRITICAL = "קריטי"

class ProtocolType(str, Enum):
    ACLS = "ACLS"
    BLS = "BLS"
    PALS = "PALS"
    TRAUMA = "TRAUMA"

class VitalSigns(BaseModel):
    heart_rate: Optional[str] = Field(None, alias="❤️ דופק")
    respiratory_rate: Optional[str] = Field(None, alias="🫁 נשימות")
    temperature: Optional[str] = Field(None, alias="🌡️ חום")
    blood_pressure: Optional[str] = Field(None, alias="⚡ לחץ דם")

class Action(BaseModel):
    action: str
    details: str
    references: Optional[List[str]] = None
    vital_signs: Optional[Dict[str, VitalSigns]] = None

class Step(BaseModel):
    step: int
    description: str
    actions: List[Action]

class SimulationRequest(BaseModel):
    title: str
    actors: List[str]
    steps: List[Step]

class NextStep(BaseModel):
    action: str
    protocol_reference: str
    expected_outcome: str

class SimulationFeedback(BaseModel):
    correct_actions: List[str]
    suggestions: List[str]
    protocol_adherence: float = Field(ge=0, le=100)

class CurrentState(BaseModel):
    patient_status: PatientStatus
    vital_signs: VitalSigns
    current_interventions: List[str]

class SimulationResponse(BaseModel):
    scenario_id: str
    current_state: CurrentState
    next_steps: List[NextStep]
    feedback: SimulationFeedback

class ValidationRequest(BaseModel):
    protocol_type: ProtocolType
    actions: List[str]
    patient_context: Optional[Dict[str, Union[int, str, List[str]]]] = None

class ValidationFeedbackStep(BaseModel):
    step: int
    action: str
    is_correct: bool
    correction: Optional[str] = None

class ProtocolReference(BaseModel):
    protocol: str
    section: str
    details: str

class ValidationResponse(BaseModel):
    is_valid: bool
    score: float = Field(ge=0, le=100)
    feedback: Optional[List[ValidationFeedbackStep]] = None
    references: Optional[List[ProtocolReference]] = None

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/v1/healthcare/simulate", response_model=SimulationResponse)
async def simulate_scenario(request: SimulationRequest, api_key: str = Depends(get_api_key)):
    scenario_id = str(uuid.uuid4())
    
    # Example response - in production this would be handled by Ollama
    return SimulationResponse(
        scenario_id=scenario_id,
        current_state=CurrentState(
            patient_status=PatientStatus.STABLE,
            vital_signs=VitalSigns(
                **{"❤️ דופק": "72", "🫁 נשימות": "16", "🌡️ חום": "36.6", "⚡ לחץ דם": "120/80"}
            ),
            current_interventions=["בדיקת סימנים חיוניים"]
        ),
        next_steps=[
            NextStep(
                action="📋 המשך הערכה ראשונית",
                protocol_reference="🏥 מדא פרוטוקולים מתקדמים 2023, פרק 1",
                expected_outcome="השלמת הערכת מצב המטופל"
            )
        ],
        feedback=SimulationFeedback(
            correct_actions=["איסוף מידע ראשוני"],
            suggestions=["לבצע תשאול מקיף יותר"],
            protocol_adherence=85.0
        )
    )

@app.post("/v1/healthcare/validate", response_model=ValidationResponse)
async def validate_protocol(request: ValidationRequest, api_key: str = Depends(get_api_key)):
    # Example validation logic - in production this would be handled by Ollama
    return ValidationResponse(
        is_valid=True,
        score=90.0,
        feedback=[
            ValidationFeedbackStep(
                step=1,
                action="בדיקת סימנים חיוניים",
                is_correct=True
            )
        ],
        references=[
            ProtocolReference(
                protocol="ACLS",
                section="Initial Assessment",
                details="Standard vital signs assessment protocol"
            )
        ]
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 