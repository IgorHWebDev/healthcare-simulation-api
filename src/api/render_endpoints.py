"""
Render API endpoints for healthcare operations.
These endpoints are specifically optimized for Render deployment and M3 integration.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
import os

from .healthcare.operations import HealthcareOperations
from .healthcare.models import (
    PatientData,
    ClinicalPrediction,
    AnalysisRequest,
    HealthcareResponse
)
from .security.auth import get_current_user, User
from .m3.optimizer import M3Optimizer

# Initialize router
router = APIRouter(prefix="/api/v1/render")

# Get database configuration from environment
DB_USER = os.getenv("DB_USER", "healthcare")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "healthcare_db")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

# Initialize database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize healthcare operations
ops = HealthcareOperations(database_url=DATABASE_URL)

@router.post("/analyze/patient/{patient_id}", response_model=HealthcareResponse)
async def analyze_patient_scenario(
    patient_id: UUID,
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> HealthcareResponse:
    """
    Analyze patient scenario using M3-optimized processing.
    This endpoint leverages Metal framework acceleration for rapid analysis.
    """
    try:
        # Process the scenario
        response = await ops.process_patient_scenario(
            patient_id=patient_id,
            analysis_type=analysis_request.analysis_type,
            parameters=analysis_request.parameters
        )
        
        # Schedule background task for extended analysis
        background_tasks.add_task(
            _perform_extended_analysis,
            patient_id,
            analysis_request
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing patient scenario: {str(e)}"
        )

@router.post("/batch/analyze", response_model=List[HealthcareResponse])
async def batch_analyze_patients(
    patient_ids: List[UUID],
    analysis_request: AnalysisRequest,
    current_user: User = Depends(get_current_user)
) -> List[HealthcareResponse]:
    """
    Perform batch analysis on multiple patients using M3 optimization.
    Utilizes parallel processing for improved performance.
    """
    responses = []
    async with M3Optimizer().optimize_batch_processing() as optimizer:
        for patient_id in patient_ids:
            try:
                response = await ops.process_patient_scenario(
                    patient_id=patient_id,
                    analysis_type=analysis_request.analysis_type,
                    parameters=analysis_request.parameters
                )
                responses.append(response)
            except Exception as e:
                responses.append(
                    HealthcareResponse(
                        status="error",
                        message=f"Error processing patient {patient_id}: {str(e)}",
                        data=None
                    )
                )
    
    return responses

@router.get("/report/patient/{patient_id}", response_model=HealthcareResponse)
async def get_patient_report(
    patient_id: UUID,
    report_type: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
) -> HealthcareResponse:
    """
    Generate comprehensive patient report with M3-optimized analytics.
    Supports various report types and date ranges.
    """
    try:
        # Query patient data
        patient_data = await ops._query_patient_data(patient_id)
        
        # Perform analysis based on report type
        analysis_results = await ops._perform_deep_analysis(
            patient_data=patient_data,
            analysis_type=f"report_{report_type}",
            parameters={
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        )
        
        # Generate report
        report = await ops._generate_report(
            patient_id=patient_id,
            analysis_results=analysis_results
        )
        
        return HealthcareResponse(
            status="success",
            message="Patient report generated successfully",
            data={
                "patient": patient_data.dict(),
                "report": report
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating patient report: {str(e)}"
        )

@router.post("/predict/clinical", response_model=HealthcareResponse)
async def predict_clinical_outcome(
    patient_id: UUID,
    prediction_params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> HealthcareResponse:
    """
    Generate clinical predictions using M3-optimized machine learning models.
    Leverages Metal framework for accelerated inference.
    """
    try:
        # Process prediction scenario
        response = await ops.process_patient_scenario(
            patient_id=patient_id,
            analysis_type="clinical_prediction",
            parameters=prediction_params
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating clinical prediction: {str(e)}"
        )

@router.post("/optimize/treatment", response_model=HealthcareResponse)
async def optimize_treatment_plan(
    patient_id: UUID,
    treatment_params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> HealthcareResponse:
    """
    Optimize treatment plans using M3 acceleration and quantum-inspired algorithms.
    Considers multiple factors for personalized treatment optimization.
    """
    try:
        # Process treatment optimization
        response = await ops.process_patient_scenario(
            patient_id=patient_id,
            analysis_type="treatment_optimization",
            parameters=treatment_params
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error optimizing treatment plan: {str(e)}"
        )

async def _perform_extended_analysis(
    patient_id: UUID,
    analysis_request: AnalysisRequest
) -> None:
    """
    Perform extended background analysis for deeper insights.
    This runs asynchronously after the initial analysis.
    """
    try:
        # Perform extended analysis with higher optimization level
        await ops.process_patient_scenario(
            patient_id=patient_id,
            analysis_type=f"{analysis_request.analysis_type}_extended",
            parameters={
                **analysis_request.parameters,
                "optimization_level": "maximum",
                "include_historical_data": True,
                "run_advanced_models": True
            }
        )
    except Exception as e:
        # Log error but don't raise it since this is a background task
        logger.error(f"Error in extended analysis for patient {patient_id}: {str(e)}")
