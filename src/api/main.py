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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key."""
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

async def verify_api_key_middleware(request: Request, call_next):
    """Middleware to verify API key."""
    try:
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
            
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key required"}
            )
            
        if api_key != os.getenv("API_KEY"):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"}
            )
            
        return await call_next(request)
        
    except Exception as e:
        logger.error(f"Error in API key middleware: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

app.middleware("http")(verify_api_key_middleware)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the FastAPI application."""
    try:
        # Initialize database
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
        # Initialize M3 optimizations
        if os.getenv("M3_OPTIMIZER_ENABLED", "true").lower() == "true":
            logger.info("M3 optimizations enabled")
            os.environ["VECLIB_MAXIMUM_THREADS"] = "8"
            
        # Initialize Metal framework
        if os.getenv("METAL_FRAMEWORK_ENABLED", "true").lower() == "true":
            logger.info("Metal framework enabled")
            
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        logger.info("Shutting down application")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

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
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database_connection": "ok",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "m3_optimizer": os.getenv("M3_OPTIMIZER_ENABLED", "true"),
            "metal_framework": os.getenv("METAL_FRAMEWORK_ENABLED", "true")
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.post("/api/v1/patients", status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    patient_data: PatientCreateRequest,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """Create a new patient record."""
    try:
        ops = HealthcareOperations(DATABASE_URL)
        patient_id = await ops.create_patient(patient_data)
        
        return {
            "status": "success",
            "message": "Patient created successfully",
            "patient_id": str(patient_id),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating patient: {str(e)}"
        )

@app.post("/api/v1/patients/{patient_id}/analyze")
async def analyze_patient(
    patient_id: UUID,
    analysis_request: AnalysisRequest,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """Process a patient scenario through the healthcare simulation model."""
    try:
        ops = HealthcareOperations(DATABASE_URL)
        analysis_result = await ops.analyze_patient(
            patient_id,
            analysis_request
        )
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing patient {patient_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing patient: {str(e)}"
        )

# Include Render-optimized endpoints
logger.info("Including healthcare router with prefix: /api/v1")
app.include_router(
    render_router,
    prefix="/api/v1",
    dependencies=[Depends(get_api_key)]
)
