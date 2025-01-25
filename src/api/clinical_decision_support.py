"""
Clinical Decision Support System with API Integration.
"""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import numpy as np
from pathlib import Path

from .healthcare_api_integration import HealthcareAPIIntegration
from ..utils.m3_optimization import M3Optimizer
from ..security.quantum_safe import QuantumSafeEncryption

logger = logging.getLogger(__name__)

class ClinicalDecisionSupport:
    """Clinical Decision Support System."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize CDS with configuration."""
        self.config = config
        self.api = HealthcareAPIIntegration(config.get("api", {}))
        self.m3_optimizer = M3Optimizer()
        self.encryption = QuantumSafeEncryption()
        self._setup_logging()

    async def get_treatment_recommendations(
        self, subject_id: int, condition_code: str
    ) -> Dict[str, Any]:
        """Get treatment recommendations based on patient data and guidelines."""
        try:
            with self.m3_optimizer.optimize_processing():
                # Get patient data in FHIR format
                patient_data = await self.api.get_patient_fhir(subject_id)
                
                # Get clinical guidelines
                guidelines = await self.api.get_clinical_guidelines(condition_code)
                
                # Generate recommendations
                recommendations = await self._generate_recommendations(
                    patient_data, guidelines
                )
                
                return recommendations
        except Exception as e:
            logger.error(f"Treatment recommendations failed: {e}")
            return {}

    async def analyze_drug_interactions(
        self, medications: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze potential drug interactions."""
        try:
            interactions = []
            for i, med1 in enumerate(medications):
                for med2 in medications[i+1:]:
                    interaction = await self._check_drug_interaction(
                        med1["code"], med2["code"]
                    )
                    if interaction:
                        interactions.append(interaction)
            
            return {
                "interactions_found": len(interactions) > 0,
                "interactions": interactions,
                "severity_level": self._calculate_severity_level(interactions)
            }
        except Exception as e:
            logger.error(f"Drug interaction analysis failed: {e}")
            return {}

    async def evaluate_lab_trends(
        self, subject_id: int, lab_codes: List[str]
    ) -> Dict[str, Any]:
        """Evaluate laboratory result trends."""
        try:
            with self.m3_optimizer.optimize_analysis():
                # Get lab observations
                patient_data = await self.api.get_patient_fhir(subject_id)
                lab_data = self._extract_lab_data(patient_data, lab_codes)
                
                # Analyze trends
                trends = self._analyze_lab_trends(lab_data)
                
                # Get reference ranges
                ref_ranges = await self._get_reference_ranges(lab_codes)
                
                return {
                    "trends": trends,
                    "reference_ranges": ref_ranges,
                    "alerts": self._generate_lab_alerts(trends, ref_ranges)
                }
        except Exception as e:
            logger.error(f"Lab trend evaluation failed: {e}")
            return {}

    async def predict_outcomes(
        self, subject_id: int, condition_code: str
    ) -> Dict[str, Any]:
        """Predict patient outcomes based on clinical data."""
        try:
            with self.m3_optimizer.optimize_prediction():
                # Get patient data
                patient_data = await self.api.get_patient_fhir(subject_id)
                
                # Extract features
                features = self._extract_prediction_features(patient_data)
                
                # Get condition-specific model
                model = await self._load_prediction_model(condition_code)
                
                # Generate predictions
                predictions = model.predict(features)
                
                return {
                    "mortality_risk": float(predictions["mortality"]),
                    "readmission_risk": float(predictions["readmission"]),
                    "los_prediction": float(predictions["length_of_stay"]),
                    "complications_risk": predictions["complications"]
                }
        except Exception as e:
            logger.error(f"Outcome prediction failed: {e}")
            return {}

    async def _generate_recommendations(
        self, patient_data: Dict, guidelines: Dict
    ) -> Dict[str, Any]:
        """Generate treatment recommendations."""
        try:
            # Extract relevant patient factors
            factors = self._extract_patient_factors(patient_data)
            
            # Match guidelines to patient factors
            matched_guidelines = self._match_guidelines(factors, guidelines)
            
            # Generate personalized recommendations
            recommendations = []
            for guideline in matched_guidelines:
                recommendation = {
                    "type": guideline["type"],
                    "recommendation": guideline["recommendation"],
                    "evidence_level": guideline["evidence_level"],
                    "rationale": self._generate_rationale(
                        guideline, factors
                    )
                }
                recommendations.append(recommendation)
            
            return {
                "recommendations": recommendations,
                "patient_factors": factors,
                "guideline_matches": len(matched_guidelines)
            }
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {}

    def _analyze_lab_trends(self, lab_data: Dict) -> Dict[str, Any]:
        """Analyze laboratory result trends."""
        trends = {}
        for code, values in lab_data.items():
            if len(values) > 1:
                trend = {
                    "direction": self._calculate_trend_direction(values),
                    "magnitude": self._calculate_trend_magnitude(values),
                    "variability": np.std(values),
                    "last_value": values[-1],
                    "mean": np.mean(values)
                }
                trends[code] = trend
        return trends

    def _setup_logging(self):
        """Configure CDS logging."""
        handler = logging.FileHandler("clinical_decision_support.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
