"""
Healthcare API endpoints optimized for M3 silicon and Metal framework.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import logging
import json

from src.api.healthcare.operations import HealthcareOperations
from src.api.healthcare.models import (
    PatientData,
    ClinicalPrediction,
    AnalysisRequest,
    PatientCreateRequest,
    SimulationRequest,
    ValidationRequest
)
from src.api.auth import verify_api_key
from src.api.security.auth import get_current_user, User

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    tags=["healthcare"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(verify_api_key)]
)

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

# Log router initialization
logger.info("Initializing healthcare router with endpoints:")
for route in router.routes:
    logger.info(f"Route: {route.path} [{route.methods}]")

@router.post("/healthcare/patients", status_code=201)
async def create_patient(
    request: Request,
    patient_request: PatientCreateRequest
) -> Dict[str, Any]:
    """Create a new patient record."""
    try:
        logger.info(f"Processing create_patient request")
        logger.debug(f"Request path: {request.url.path}")
        logger.debug(f"Patient request: {json.dumps(patient_request.dict(), indent=2)}")
        
        patient_id = await ops.create_patient(patient_request.patient_data)
        
        response_data = {
            "status": "success",
            "message": "Patient created successfully",
            "patient_id": str(patient_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Successfully created patient with ID: {patient_id}")
        return response_data
    except Exception as e:
        error_msg = f"Error creating patient: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/healthcare/analyze/{patient_id}")
async def analyze_patient_scenario(
    request: Request,
    patient_id: UUID,
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Process a patient scenario through the healthcare simulation model.
    This endpoint leverages Metal framework acceleration for rapid analysis.
    """
    try:
        logger.info(f"Processing analyze_patient request for patient {patient_id}")
        logger.debug(f"Request path: {request.url.path}")
        logger.debug(f"Analysis request: {json.dumps(analysis_request.dict(), indent=2)}")
        
        analysis_result = await ops.analyze_patient_scenario(
            patient_id,
            analysis_request,
            background_tasks
        )
        
        response_data = {
            "status": "success",
            "message": "Analysis completed successfully",
            "analysis_id": analysis_result.analysis_id,
            "predictions": analysis_result.predictions,
            "recommendations": analysis_result.recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Successfully completed analysis for patient {patient_id}")
        logger.debug(f"Analysis result: {json.dumps(response_data, indent=2)}")
        return response_data
    except Exception as e:
        error_msg = f"Error analyzing patient {patient_id}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/healthcare/simulate")
async def simulate_scenario(
    request: Request,
    simulation_request: SimulationRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Simulate patient scenario using M3-optimized processing.
    This endpoint leverages Metal framework acceleration for rapid simulation.
    """
    logger.info(f"Processing simulate_scenario request")
    logger.debug(f"Request path: {request.url.path}")
    logger.debug(f"Simulation request: {json.dumps(simulation_request.dict(), indent=2)}")
    
    try:
        simulation_result = await ops.simulate_scenario(
            simulation_request,
            background_tasks
        )
        
        response_data = {
            "status": "success",
            "message": "Simulation completed successfully",
            "simulation_id": simulation_result.simulation_id,
            "results": simulation_result.results,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Successfully completed simulation")
        logger.debug(f"Simulation result: {json.dumps(response_data, indent=2)}")
        return response_data
    except Exception as e:
        error_msg = f"Error simulating scenario: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/healthcare/validate")
async def validate_protocol(
    request: Request,
    validation_request: ValidationRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Validate patient protocol using M3-optimized processing.
    This endpoint leverages Metal framework acceleration for rapid validation.
    """
    logger.info(f"Processing validate_protocol request")
    logger.debug(f"Request path: {request.url.path}")
    logger.debug(f"Validation request: {json.dumps(validation_request.dict(), indent=2)}")
    
    try:
        validation_result = await ops.validate_protocol(
            validation_request,
            background_tasks
        )
        
        response_data = {
            "status": "success",
            "message": "Validation completed successfully",
            "validation_id": validation_result.validation_id,
            "results": validation_result.results,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Successfully completed validation")
        logger.debug(f"Validation result: {json.dumps(response_data, indent=2)}")
        return response_data
    except Exception as e:
        error_msg = f"Error validating protocol: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )
