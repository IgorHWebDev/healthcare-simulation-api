"""Models for Healthcare Simulation API."""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum

class PatientStatus(str, Enum):
    """Patient status enum."""
    STABLE = "יציב"
    UNSTABLE = "לא יציב"
    CRITICAL = "קריטי"

class ProtocolType(str, Enum):
    """Protocol type enum."""
    ACLS = "ACLS"
    BLS = "BLS"
    PALS = "PALS"
    TRAUMA = "TRAUMA"

class VitalSigns(BaseModel):
    """Model for vital signs."""
    heart_rate: str = Field(..., alias="❤️ דופק")
    respiratory_rate: str = Field(..., alias="🫁 נשימות")
    temperature: str = Field(..., alias="🌡️ חום")
    blood_pressure: str = Field(..., alias="⚡ לחץ דם")

    class Config:
        """Pydantic config."""
        populate_by_name = True
        allow_population_by_field_name = True

class Action(BaseModel):
    """Model for actions."""
    action: str
    details: str
    references: Optional[List[str]] = None

class Step(BaseModel):
    """Model for steps."""
    step: int
    description: str
    actions: List[Action]

class SimulationRequest(BaseModel):
    """Model for simulation requests."""
    title: str
    actors: List[str]
    steps: List[Step]

class NextStep(BaseModel):
    """Model for next steps."""
    action: str
    protocol_reference: str
    expected_outcome: str

class SimulationFeedback(BaseModel):
    """Model for simulation feedback."""
    correct_actions: List[str]
    suggestions: List[str]
    protocol_adherence: float = Field(ge=0, le=100)

class CurrentState(BaseModel):
    """Model for current state."""
    patient_status: PatientStatus
    vital_signs: VitalSigns
    current_interventions: List[str]

class SimulationResponse(BaseModel):
    """Model for simulation responses."""
    scenario_id: str
    current_state: CurrentState
    next_steps: List[NextStep]
    feedback: SimulationFeedback

class ValidationRequest(BaseModel):
    """Model for validation requests."""
    protocol_type: ProtocolType
    actions: List[str]
    patient_context: Optional[Dict[str, Union[int, str, List[str]]]] = None

class ValidationFeedbackStep(BaseModel):
    """Model for validation feedback steps."""
    step: int
    action: str
    is_correct: bool
    correction: Optional[str] = None

class ProtocolReference(BaseModel):
    """Model for protocol references."""
    protocol: str
    section: str
    details: str

class ValidationResponse(BaseModel):
    """Model for validation responses."""
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