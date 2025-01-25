"""
Healthcare Operations Module
Handles complete cycle of healthcare data operations including querying, analysis, and reporting.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .models import (
    PatientData, 
    ClinicalPrediction,
    AnalysisRequest,
    HealthcareResponse
)
from ..database.models import (
    Patient,
    Diagnosis,
    Medication,
    LabResult,
    ClinicalPrediction as DBClinicalPrediction
)
from ..m3.optimizer import M3Optimizer

logger = logging.getLogger(__name__)

class HealthcareOperations:
    def __init__(self, database_url: str):
        """Initialize healthcare operations with database connection."""
        self.engine = create_engine(database_url)
        self.m3_optimizer = M3Optimizer()

    async def process_patient_scenario(
        self,
        patient_id: UUID,
        analysis_type: str,
        parameters: Dict[str, Any]
    ) -> HealthcareResponse:
        """
        Process a complete patient scenario including data query, analysis, and storage.
        
        Args:
            patient_id: UUID of the patient
            analysis_type: Type of analysis to perform
            parameters: Additional parameters for analysis
            
        Returns:
            HealthcareResponse containing analysis results and recommendations
        """
        try:
            # Step 1: Query patient data
            patient_data = await self._query_patient_data(patient_id)
            
            # Step 2: Perform deep analysis
            analysis_results = await self._perform_deep_analysis(
                patient_data,
                analysis_type,
                parameters
            )
            
            # Step 3: Update database with results
            await self._update_database(patient_id, analysis_results)
            
            # Step 4: Generate report
            report = await self._generate_report(patient_id, analysis_results)
            
            return HealthcareResponse(
                status="success",
                message="Patient scenario processed successfully",
                data={
                    "patient": patient_data.dict(),
                    "analysis": analysis_results,
                    "report": report
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing patient scenario: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing patient scenario: {str(e)}"
            )

    async def _query_patient_data(self, patient_id: UUID) -> PatientData:
        """Query comprehensive patient data from the database."""
        with Session(self.engine) as session:
            # Query patient basic info
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                raise HTTPException(
                    status_code=404,
                    detail=f"Patient {patient_id} not found"
                )
            
            # Query related data
            diagnoses = session.query(Diagnosis).filter(
                Diagnosis.patient_id == patient_id
            ).all()
            
            medications = session.query(Medication).filter(
                Medication.patient_id == patient_id
            ).all()
            
            lab_results = session.query(LabResult).filter(
                LabResult.patient_id == patient_id
            ).all()
            
            return PatientData(
                patient_id=patient.id,
                mrn=patient.mrn,
                first_name=patient.first_name,
                last_name=patient.last_name,
                date_of_birth=patient.date_of_birth,
                gender=patient.gender,
                diagnoses=[d.icd_code for d in diagnoses],
                medications=[m.medication_name for m in medications],
                lab_results=[{
                    "test": l.test_name,
                    "value": l.value,
                    "unit": l.unit,
                    "date": l.test_date
                } for l in lab_results]
            )

    async def _perform_deep_analysis(
        self,
        patient_data: PatientData,
        analysis_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform deep analysis using M3 optimization.
        
        This method uses the M3 optimizer to analyze patient data and generate
        predictions and recommendations.
        """
        async with self.m3_optimizer.optimize_analysis() as optimizer:
            # Prepare data for analysis
            analysis_data = {
                "patient": patient_data.dict(),
                "type": analysis_type,
                "parameters": parameters
            }
            
            # Perform optimized analysis
            results = await optimizer.analyze(analysis_data)
            
            # Extract key metrics and predictions
            predictions = results.get("predictions", {})
            risk_factors = results.get("risk_factors", [])
            recommendations = results.get("recommendations", [])
            
            return {
                "predictions": predictions,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "confidence_score": results.get("confidence_score", 0.0),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

    async def _update_database(
        self,
        patient_id: UUID,
        analysis_results: Dict[str, Any]
    ) -> None:
        """Update database with analysis results."""
        with Session(self.engine) as session:
            # Create new clinical prediction record
            prediction = DBClinicalPrediction(
                patient_id=patient_id,
                prediction_type="comprehensive_analysis",
                prediction_value=analysis_results["predictions"].get("risk_score", 0.0),
                confidence_score=analysis_results["confidence_score"],
                factors=analysis_results["risk_factors"],
                prediction_date=datetime.utcnow()
            )
            
            session.add(prediction)
            session.commit()

    async def _generate_report(
        self,
        patient_id: UUID,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive report from analysis results."""
        # Format predictions for reporting
        predictions_report = {
            k: f"{v:.2f}" if isinstance(v, float) else v
            for k, v in analysis_results["predictions"].items()
        }
        
        # Format risk factors with severity levels
        risk_factors_report = [
            {
                "factor": factor,
                "severity": "high" if idx < 3 else "medium" if idx < 6 else "low"
            }
            for idx, factor in enumerate(analysis_results["risk_factors"])
        ]
        
        # Generate action items from recommendations
        action_items = [
            {
                "action": rec,
                "priority": "high" if idx < 2 else "medium" if idx < 4 else "low",
                "status": "pending"
            }
            for idx, rec in enumerate(analysis_results["recommendations"])
        ]
        
        return {
            "summary": {
                "analysis_type": "comprehensive_analysis",
                "timestamp": analysis_results["analysis_timestamp"],
                "confidence_score": f"{analysis_results['confidence_score']:.2f}"
            },
            "predictions": predictions_report,
            "risk_factors": risk_factors_report,
            "action_items": action_items,
            "metadata": {
                "patient_id": str(patient_id),
                "generated_at": datetime.utcnow().isoformat(),
                "model_version": "M3-2025.1"
            }
        }
