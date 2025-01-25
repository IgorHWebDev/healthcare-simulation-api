"""
Main FastAPI application for healthcare simulation API.
Optimized for M3 silicon chip and Metal framework acceleration.
"""
from fastapi import FastAPI, HTTPException, Depends, Security, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import logging
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pydantic import ValidationError

# Add src directory to Python path
src_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if src_path not in sys.path:
    sys.path.append(src_path)

from src.api.healthcare.operations import HealthcareOperations
from src.api.healthcare.models import (
    PatientData,
    ClinicalPrediction,
    AnalysisRequest,
    HealthcareResponse,
    PatientCreateRequest
)
from src.api.database.models import Base
from src.api.security.auth import User, create_access_token, get_current_user
from src.api.render_endpoints import router as render_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get database configuration from environment
DB_USER = os.getenv("DB_USER", "healthcare")
DB_PASSWORD = os.getenv("DB_PASSWORD", "healthcare")
DB_NAME = os.getenv("DB_NAME", "healthcare_db")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# API Key configuration
API_KEY = os.getenv("API_KEY", "rnd_Z3muoAk3bhxOVj1laxjUV6Uv8hL")
api_key_header = APIKeyHeader(name="X-API-Key")

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="API for healthcare simulation and analysis, optimized for M3 silicon",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize security
async def verify_api_key_middleware(request: Request, call_next):
    """Verify API key middleware."""
    path = request.url.path
    if path.startswith("/health"):
        logger.debug(f"Skipping API key verification for excluded path: {path}")
        response = await call_next(request)
        return response

    try:
        if "X-API-Key" not in request.headers:
            logger.warning(f"Missing API key for path: {path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "API key is missing"}
            )
        api_key = request.headers["X-API-Key"]
        if api_key != API_KEY:
            logger.warning(f"Invalid API key for path: {path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid API key"}
            )
        logger.debug(f"API key verified for path: {path}")
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"API key verification failed for path {path}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error during authentication"}
        )

app.middleware("http")(verify_api_key_middleware)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the FastAPI application."""
    # Initialize database
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database initialization error: {str(e)}")
        
    # Initialize healthcare operations
    app.state.healthcare_ops = HealthcareOperations(DATABASE_URL)
    logger.info("Healthcare operations initialized")
    
    yield
    
    # Cleanup
    logger.info("Shutting down application")

# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable"
        )

# Patient simulation endpoints
@app.post("/api/v1/healthcare/patients", response_model=HealthcareResponse, status_code=201)
async def create_patient(
    request: PatientCreateRequest
) -> HealthcareResponse:
    """Create a new patient record."""
    try:
        logging.info("Received patient data: %s", request.model_dump_json())
        patient = await app.state.healthcare_ops.create_patient(request.patient_data)
        return HealthcareResponse(
            status="success",
            message="Patient created successfully",
            data={"patient_id": str(patient.id)}
        )
    except ValidationError as e:
        logging.error("Validation error: %s", e.errors())
        raise HTTPException(
            status_code=422,
            detail=f"Invalid request data: {e.errors()}"
        )
    except Exception as e:
        logging.error("Failed to create patient: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create patient: {str(e)}"
        )

@app.post("/api/v1/healthcare/analyze/{patient_id}", response_model=HealthcareResponse)
async def analyze_patient(
    patient_id: UUID,
    analysis_request: AnalysisRequest
) -> HealthcareResponse:
    """
    Process a patient scenario through the healthcare simulation model.
    Uses LM Studio for analysis and predictions.
    """
    try:
        result = await app.state.healthcare_ops.process_patient_scenario(
            patient_id,
            analysis_request.analysis_type,
            analysis_request.parameters or {}
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing patient {patient_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing patient: {str(e)}"
        )

# Include Render-optimized endpoints
logger.info("Including healthcare router with prefix: /api/v1")
app.include_router(
    render_router,
    prefix="/api/v1",
    tags=["healthcare"]
)
