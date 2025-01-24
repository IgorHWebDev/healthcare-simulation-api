from typing import List, Optional, Dict
from pydantic import BaseModel, Field
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
    pulse: Optional[str] = Field(None, alias="❤️ דופק")
    breathing: Optional[str] = Field(None, alias="🫁 נשימות")
    temperature: Optional[str] = Field(None, alias="🌡️ חום")
    blood_pressure: Optional[str] = Field(None, alias="⚡ לחץ דם")

class VitalSignsMonitoring(BaseModel):
    pre_assessment: Optional[VitalSigns] = None
    during_treatment: Optional[VitalSigns] = None

class Action(BaseModel):
    action: str
    details: str
    references: Optional[List[str]] = None
    vital_signs: Optional[VitalSignsMonitoring] = None

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
    vital_signs: Optional[VitalSigns] = None
    current_interventions: List[str]

class SimulationResponse(BaseModel):
    scenario_id: str
    current_state: CurrentState
    next_steps: List[NextStep]
    feedback: SimulationFeedback

class PatientContext(BaseModel):
    age: Optional[int] = None
    presenting_condition: Optional[str] = None
    contraindications: Optional[List[str]] = None

class ValidationRequest(BaseModel):
    protocol_type: ProtocolType
    actions: List[str]
    patient_context: Optional[PatientContext] = None

class ValidationFeedback(BaseModel):
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
    feedback: Optional[List[ValidationFeedback]] = None
    references: Optional[List[ProtocolReference]] = None 