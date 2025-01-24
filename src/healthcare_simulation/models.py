from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum

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
    heart_rate: str = Field(..., alias="❤️ דופק", pattern="^[0-9]{1,3}$|^Absent$|^Irregular$")
    respiratory_rate: str = Field(..., alias="🫁 נשימות", pattern="^[0-9]{1,2}$|^Absent$|^Labored$")
    temperature: str = Field(..., alias="🌡️ חום", pattern="^[3-4][0-9]\\.[0-9]$|^Normal$")
    blood_pressure: str = Field(..., alias="⚡ לחץ דם", pattern="^[0-9]{2,3}\\/[0-9]{2,3}$|^Undetectable$")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class Action(BaseModel):
    action: str
    details: str
    references: Optional[List[str]] = None

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

current_state = CurrentState(
    patient_status=PatientStatus.UNSTABLE,
    vital_signs=VitalSigns(**{
        "❤️ דופק": "72",
        "🫁 נשימות": "16",
        "🌡️ חום": "36.5",
        "⚡ לחץ דם": "120/80"
    }),
    current_interventions=[]
) 