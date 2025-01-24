from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import uuid
from healthcare_simulation.models import *

app = FastAPI(
    title="Healthcare Simulation API",
    description="Healthcare Simulation API powered by Ollama multi-model support",
    version="0.1.0"
)

# Security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header or api_key_header != "test_api_key":
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key_header

@app.get("/")
async def root():
    return {"message": "Healthcare Simulation API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/v1/healthcare/simulate")
async def simulate_scenario(
    request: SimulationRequest,
    api_key: str = Depends(get_api_key)
):
    scenario_id = str(uuid.uuid4())
    return {
        "scenario_id": scenario_id,
        "current_state": {
            "patient_status": "יציב",
            "vital_signs": {
                "❤️ דופק": "72",
                "🫁 נשימות": "16",
                "🌡️ חום": "36.5",
                "⚡ לחץ דם": "120/80"
            },
            "current_interventions": []
        },
        "next_steps": [
            {
                "action": "בדיקת סימנים חיוניים",
                "protocol_reference": "AHA ACLS Guidelines 2020",
                "expected_outcome": "הערכת מצב המטופל"
            }
        ],
        "feedback": {
            "correct_actions": ["הערכה ראשונית מהירה", "בדיקת הכרה"],
            "suggestions": ["לשקול חיבור מוניטור", "להכין ציוד החייאה"],
            "protocol_adherence": 85.0
        }
    }

@app.post("/v1/healthcare/validate")
async def validate_protocol(
    request: ValidationRequest,
    api_key: str = Depends(get_api_key)
):
    return {
        "is_valid": True,
        "score": 95.0,
        "feedback": [
            {
                "step": 1,
                "action": request.actions[0],
                "is_correct": True
            }
        ],
        "references": [
            {
                "protocol": request.protocol_type,
                "section": "Initial Assessment",
                "details": "Standard protocol for initial patient assessment"
            }
        ]
    } 