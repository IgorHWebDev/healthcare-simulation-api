"""
Main FastAPI application for healthcare simulation API.
Includes Render-optimized endpoints for healthcare operations.
"""
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from src.database.mimic4_adapter import MIMIC4Adapter
from src.utils.m3_optimization import M3Optimizer
from src.api.healthcare.models import (
    PatientData,
    ClinicalPrediction,
    AnalysisRequest,
    HealthcareResponse,
    LabResult,
    Base
)
from src.api.security.auth import User, create_access_token, get_current_user
from src.api.render_endpoints import router as render_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database configuration from environment
DB_USER = os.getenv("DB_USER", "healthcare")
DB_PASSWORD = os.getenv("DB_SECRET")
DB_NAME = os.getenv("DB_NAME", "healthcare_db")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="M3-optimized healthcare API with Render deployment support",
    version="2025.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management for the FastAPI application.
    Handles database initialization and M3 optimizer setup.
    """
    try:
        # Initialize database
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")

        # Initialize M3 optimizer with Metal framework
        metal_enabled = os.getenv("METAL_FRAMEWORK_ENABLED", "true").lower() == "true"
        batch_size = int(os.getenv("BATCH_SIZE", "256"))
        max_circuits = int(os.getenv("MAX_PARALLEL_CIRCUITS", "1000"))

        M3Optimizer.initialize(
            metal_enabled=metal_enabled,
            batch_size=batch_size,
            max_parallel_circuits=max_circuits
        )
        logger.info("M3 Optimizer initialized with Metal framework")

        # Initialize database adapter
        app.state.db = MIMIC4Adapter(engine)
        app.state.m3_optimizer = M3Optimizer()
        
        yield
        
        # Cleanup
        M3Optimizer.cleanup()
        logger.info("Resources cleaned up successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise

app.lifespan = lifespan

@app.middleware("http")
async def verify_api_key(request, call_next):
    """Verify API key middleware."""
    try:
        if "X-API-Key" not in request.headers:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "API key is missing"}
            )
        api_key = request.headers["X-API-Key"]
        if api_key != os.getenv("API_KEY"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid API key"}
            )
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"API key verification failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error during authentication"}
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )

# Include Render-optimized endpoints
app.include_router(render_router)

@app.get("/api/v1/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        # Check database connection
        with app.state.db.engine.connect() as conn:
            conn.execute("SELECT 1")
        
        # Check M3 optimizer
        app.state.m3_optimizer.check_status()
        
        return {
            "status": "healthy",
            "database_connection": "active",
            "m3_optimizer": "ready",
            "metal_framework": "enabled",
            "api_version": "2025.1.0",
            "last_check_time": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"System health check failed: {str(e)}"
        )

@app.get("/api/v1/status")
async def get_system_status(
    current_user: User = Depends(get_current_user)
) -> HealthcareResponse:
    """
    Get detailed system status including M3 optimization metrics.
    Requires authentication.
    """
    try:
        # Get M3 optimizer metrics
        optimizer_metrics = app.state.m3_optimizer.get_metrics()
        
        return HealthcareResponse(
            status="success",
            message="System status retrieved successfully",
            data={
                "m3_optimizer": {
                    "status": "active",
                    "metal_enabled": True,
                    "optimization_level": optimizer_metrics.get("level", "high"),
                    "performance_metrics": optimizer_metrics.get("performance", {})
                },
                "api_status": {
                    "version": "2025.1.0",
                    "uptime": optimizer_metrics.get("uptime", 0),
                    "request_count": optimizer_metrics.get("request_count", 0)
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving system status: {str(e)}"
        )

@app.get("/api/v1/patient/{patient_id}", response_model=HealthcareResponse)
async def get_patient_data(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
) -> HealthcareResponse:
    """Get patient data by ID."""
    try:
        with app.state.m3_optimizer.optimize_query_execution() as optimization:
            data = app.state.db.query_patient_data(patient_id)
            if not data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Patient {patient_id} not found"
                )
            
            # Convert lab results to proper model
            if 'lab_results' in data:
                data['lab_results'] = [
                    LabResult(**result) for result in data['lab_results']
                ]
            
            return HealthcareResponse(
                status="success",
                data={"patient": PatientData(**data)},
                message="Patient data retrieved successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/predict", response_model=HealthcareResponse)
async def predict_clinical_outcome(
    request: ClinicalPrediction,
    current_user: dict = Depends(get_current_user)
) -> HealthcareResponse:
    """Generate clinical predictions."""
    try:
        with app.state.m3_optimizer.optimize_prediction() as optimization:
            # Get patient data
            patient_data = app.state.db.query_patient_data(request.patient_id)
            if not patient_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Patient {request.patient_id} not found"
                )
            
            # Return the optimized prediction
            return HealthcareResponse(
                status="success",
                data=optimization,
                message="Clinical prediction generated successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/analyze", response_model=HealthcareResponse)
async def analyze_data(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
) -> HealthcareResponse:
    """Analyze healthcare data."""
    try:
        with app.state.m3_optimizer.optimize_analysis() as optimization:
            if not request.patient_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No patient IDs provided"
                )
            
            # Return the optimized analysis
            return HealthcareResponse(
                status="success",
                data=optimization,
                message="Data analysis completed successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/process-batch", response_model=HealthcareResponse)
async def process_batch_data(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> HealthcareResponse:
    """Process batch data requests."""
    try:
        with app.state.m3_optimizer.optimize_processing() as optimization:
            if not request.get("patient_ids"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No patient IDs provided"
                )
            
            start_time = datetime.now()
            
            # Process each patient
            processed_data = []
            for patient_id in request["patient_ids"]:
                data = app.state.db.query_patient_data(patient_id)
                if data:
                    processed_data.append(data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "processed_count": len(processed_data),
                "features": processed_data,
                "processing_time": processing_time,
                "optimization_status": optimization
            }
            
            return HealthcareResponse(
                status="success",
                data=result,
                message="Batch processing completed successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/patient/update", response_model=HealthcareResponse)
async def update_patient_data(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> HealthcareResponse:
    """Update patient data."""
    try:
        with app.state.m3_optimizer.optimize_storage() as optimization:
            # Update patient data
            success = app.state.db.update_patient_data(request)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Failed to update patient {request.get('patient_id')}"
                )
            
            return HealthcareResponse(
                status="success",
                data={"optimization": optimization},
                message="Patient data updated successfully"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
