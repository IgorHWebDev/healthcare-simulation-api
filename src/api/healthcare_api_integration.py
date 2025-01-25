"""
Healthcare API Integration Layer with FHIR and SMART on FHIR Support.
"""
from typing import Dict, List, Optional, Any
import httpx
import logging
from datetime import datetime
from pathlib import Path
import json

from ..database.mimic4_adapter import MIMIC4Adapter
from ..utils.m3_optimization import M3Optimizer
from ..security.quantum_safe import QuantumSafeEncryption

logger = logging.getLogger(__name__)

class HealthcareAPIIntegration:
    """Healthcare API Integration with FHIR support."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize API integration with configuration."""
        self.config = config
        self.m3_optimizer = M3Optimizer()
        self.encryption = QuantumSafeEncryption()
        self.mimic4_adapter = MIMIC4Adapter(config.get("mimic4", {}))
        self._setup_logging()

    async def get_patient_fhir(self, subject_id: int) -> Dict[str, Any]:
        """Get patient data in FHIR format."""
        try:
            with self.m3_optimizer.optimize_processing():
                # Get MIMIC-4 data
                patient_data = await self.mimic4_adapter.process_patient_data(subject_id)
                
                # Transform to FHIR
                fhir_patient = self._transform_to_fhir_patient(patient_data)
                fhir_observations = self._transform_to_fhir_observations(
                    patient_data.get("lab_results", [])
                )
                fhir_medications = self._transform_to_fhir_medications(
                    patient_data.get("prescriptions", [])
                )
                
                return {
                    "resourceType": "Bundle",
                    "type": "collection",
                    "entry": [
                        {"resource": fhir_patient},
                        {"resource": fhir_observations},
                        {"resource": fhir_medications}
                    ]
                }
        except Exception as e:
            logger.error(f"FHIR transformation failed: {e}")
            return {}

    async def submit_to_smart_on_fhir(
        self, data: Dict[str, Any], endpoint: str
    ) -> bool:
        """Submit data to SMART on FHIR endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=data,
                    headers=self._get_auth_headers()
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"SMART on FHIR submission failed: {e}")
            return False

    async def query_terminology_service(
        self, code: str, system: str
    ) -> Dict[str, Any]:
        """Query terminology service for code lookup."""
        try:
            endpoint = self.config["terminology_service_url"]
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{endpoint}/CodeSystem/$lookup",
                    params={"code": code, "system": system},
                    headers=self._get_auth_headers()
                )
                return response.json()
        except Exception as e:
            logger.error(f"Terminology service query failed: {e}")
            return {}

    async def get_clinical_guidelines(
        self, condition_code: str
    ) -> Dict[str, Any]:
        """Get clinical guidelines for condition."""
        try:
            endpoint = self.config["guidelines_service_url"]
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{endpoint}/guidelines/{condition_code}",
                    headers=self._get_auth_headers()
                )
                return response.json()
        except Exception as e:
            logger.error(f"Clinical guidelines query failed: {e}")
            return {}

    def _transform_to_fhir_patient(self, data: Dict) -> Dict[str, Any]:
        """Transform patient data to FHIR format."""
        patient = data.get("patient", {})
        return {
            "resourceType": "Patient",
            "id": str(patient.get("subject_id")),
            "gender": patient.get("gender", "unknown"),
            "birthDate": self._calculate_birth_date(
                patient.get("anchor_age"),
                patient.get("anchor_year")
            ),
            "extension": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-age",
                    "valueAge": {
                        "value": patient.get("anchor_age"),
                        "unit": "years",
                        "system": "http://unitsofmeasure.org",
                        "code": "a"
                    }
                }
            ]
        }

    def _transform_to_fhir_observations(
        self, lab_results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Transform lab results to FHIR Observations."""
        observations = []
        for lab in lab_results:
            observation = {
                "resourceType": "Observation",
                "id": str(lab.get("labevent_id")),
                "status": "final",
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": str(lab.get("itemid")),
                        "display": lab.get("label")
                    }]
                },
                "valueQuantity": {
                    "value": lab.get("valuenum"),
                    "unit": lab.get("valueuom"),
                    "system": "http://unitsofmeasure.org",
                    "code": lab.get("valueuom")
                },
                "effectiveDateTime": lab.get("charttime").isoformat(),
                "subject": {
                    "reference": f"Patient/{lab.get('subject_id')}"
                }
            }
            observations.append(observation)
        return observations

    def _transform_to_fhir_medications(
        self, prescriptions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Transform prescriptions to FHIR MedicationRequests."""
        medications = []
        for rx in prescriptions:
            medication = {
                "resourceType": "MedicationRequest",
                "id": str(rx.get("pharmacy_id")),
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": rx.get("gsn"),
                        "display": rx.get("drug")
                    }]
                },
                "subject": {
                    "reference": f"Patient/{rx.get('subject_id')}"
                },
                "authoredOn": rx.get("starttime").isoformat(),
                "dosageInstruction": [{
                    "text": f"{rx.get('dose_val_rx')} {rx.get('dose_unit_rx')}",
                    "timing": {
                        "repeat": {
                            "frequency": 1,
                            "period": 1,
                            "periodUnit": "d"
                        }
                    }
                }]
            }
            medications.append(medication)
        return medications

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.config.get('api_token')}",
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json"
        }

    def _setup_logging(self):
        """Configure API integration logging."""
        handler = logging.FileHandler("healthcare_api.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
