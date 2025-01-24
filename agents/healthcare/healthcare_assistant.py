"""
Healthcare Assistant Agent
Specialized agent for medical tasks using AutoGen integration
"""

import asyncio
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
from dataclasses import dataclass
from ..autogen.autogen_coordinator import AutoGenCoordinator
from ..autogen.model_factory import TaskType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MedicalRequest:
    type: str
    specialty: Optional[str]
    urgency: int
    patient_data: Dict[str, Any]
    consent: bool
    context: Optional[Dict[str, Any]] = None

class HealthcareAssistant:
    def __init__(self, config_path: str = "config/autogen.yaml"):
        self.coordinator = AutoGenCoordinator(config_path)
        self.specialties = self._load_specialties()
        self.terminology = self._load_terminology()

    def _load_specialties(self) -> List[str]:
        """Load supported medical specialties"""
        return self.coordinator.model_factory.config['healthcare']['specialties']

    def _load_terminology(self) -> Dict[str, bool]:
        """Load supported medical terminology systems"""
        return self.coordinator.model_factory.config['healthcare']['terminology']

    async def process_medical_request(self, request: MedicalRequest) -> Dict[str, Any]:
        """
        Process a medical request with appropriate safeguards and validations
        """
        try:
            # Validate request compliance
            if not await self._validate_request(request):
                return {
                    "status": "error",
                    "error": "Request validation failed",
                    "details": "Request does not meet compliance requirements"
                }

            # Prepare request for processing
            processed_request = await self._prepare_request(request)

            # Process through AutoGen coordinator
            response = await self.coordinator.process_healthcare_request(
                request=processed_request,
                medical_specialty=request.specialty,
                urgency_level=request.urgency
            )

            # Post-process response
            final_response = await self._post_process_response(response)

            return final_response

        except Exception as e:
            logger.error(f"Error processing medical request: {e}")
            return {
                "status": "error",
                "error": str(e),
                "request_id": id(request)
            }

    async def _validate_request(self, request: MedicalRequest) -> bool:
        """Validate medical request for compliance and completeness"""
        try:
            # Check patient consent
            if not request.consent:
                logger.warning("Patient consent not provided")
                return False

            # Validate specialty if provided
            if request.specialty and request.specialty not in self.specialties:
                logger.warning(f"Unsupported specialty: {request.specialty}")
                return False

            # Validate urgency level
            if not 1 <= request.urgency <= 5:
                logger.warning(f"Invalid urgency level: {request.urgency}")
                return False

            # Validate patient data
            if not self._validate_patient_data(request.patient_data):
                return False

            # Check compliance requirements
            return await self.coordinator.validate_compliance({
                "type": request.type,
                "patient_consent": request.consent,
                "patient_data": request.patient_data
            })

        except Exception as e:
            logger.error(f"Error validating request: {e}")
            return False

    def _validate_patient_data(self, patient_data: Dict[str, Any]) -> bool:
        """Validate patient data structure and content"""
        required_fields = {"id", "demographics", "medical_history"}
        
        try:
            # Check required fields
            if not all(field in patient_data for field in required_fields):
                logger.warning("Missing required patient data fields")
                return False

            # Validate demographics
            if not self._validate_demographics(patient_data["demographics"]):
                return False

            # Validate medical history
            if not self._validate_medical_history(patient_data["medical_history"]):
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating patient data: {e}")
            return False

    def _validate_demographics(self, demographics: Dict) -> bool:
        """Validate patient demographics data"""
        required_fields = {"age", "gender", "ethnicity"}
        return all(field in demographics for field in required_fields)

    def _validate_medical_history(self, history: Dict) -> bool:
        """Validate medical history data"""
        required_fields = {"conditions", "medications", "allergies"}
        return all(field in history for field in required_fields)

    async def _prepare_request(self, request: MedicalRequest) -> Dict[str, Any]:
        """Prepare medical request for processing"""
        return {
            "type": request.type,
            "specialty": request.specialty,
            "urgency": request.urgency,
            "patient_data": self._sanitize_patient_data(request.patient_data),
            "context": request.context or {},
            "terminology": self._get_relevant_terminology(request.type)
        }

    def _sanitize_patient_data(self, patient_data: Dict) -> Dict:
        """Remove sensitive information not needed for processing"""
        sanitized = patient_data.copy()
        sensitive_fields = {"ssn", "address", "contact", "insurance"}
        for field in sensitive_fields:
            sanitized.pop(field, None)
        return sanitized

    def _get_relevant_terminology(self, request_type: str) -> Dict[str, bool]:
        """Get relevant medical terminology systems for the request type"""
        if "diagnosis" in request_type.lower():
            return {
                "snomed_ct": self.terminology["snomed_ct"],
                "icd10": self.terminology["icd10"]
            }
        elif "medication" in request_type.lower():
            return {
                "rxnorm": self.terminology["rxnorm"]
            }
        return self.terminology

    async def _post_process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process the response from AutoGen"""
        try:
            if response["status"] != "success":
                return response

            # Add metadata
            processed_response = {
                **response,
                "timestamp": asyncio.get_event_loop().time(),
                "terminology_systems": self._get_relevant_terminology(response.get("type", "")),
                "compliance_verified": True
            }

            # Add relevant medical codes if applicable
            if "diagnosis" in processed_response.get("response", {}):
                processed_response["medical_codes"] = await self._add_medical_codes(
                    processed_response["response"]["diagnosis"]
                )

            return processed_response

        except Exception as e:
            logger.error(f"Error post-processing response: {e}")
            return response

    async def _add_medical_codes(self, diagnosis: str) -> Dict[str, List[str]]:
        """Add relevant medical codes to the diagnosis"""
        # Placeholder - implement actual medical coding logic
        return {
            "icd10": ["placeholder_icd10_code"],
            "snomed_ct": ["placeholder_snomed_code"]
        }

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current status of the healthcare assistant"""
        return {
            "agent_type": "HealthcareAssistant",
            "supported_specialties": self.specialties,
            "terminology_systems": self.terminology,
            "system_status": await self.coordinator.get_system_status(),
            "compliance_status": "active"
        } 