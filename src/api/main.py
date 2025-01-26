"""
Main FastAPI application for healthcare simulation API.
Optimized for M3 silicon chip and Metal framework acceleration.
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Security
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from uuid import UUID
from pydantic import ValidationError
import httpx
import datetime

# Add src directory to Python path
src_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(src_path)

from src.api.healthcare.models import (
    SimulationRequest,
    SimulationResponse,
    ValidationRequest,
    ValidationResponse,
    PatientStatus
)
from src.api.healthcare.operations import HealthcareOperations
from src.api.render_endpoints import router as render_router
from src.api.auth import verify_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")

# Initialize SQLAlchemy models
Base = declarative_base()

# Initialize database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = scoped_session(SessionLocal)

# Initialize healthcare operations
healthcare_ops = HealthcareOperations(DATABASE_URL)

# M3 and Metal framework optimization configuration
try:
    from Metal import MTLCreateSystemDefaultDevice
    metal_device = MTLCreateSystemDefaultDevice()
    metal_enabled = metal_device is not None
except ImportError:
    metal_enabled = False
    
M3_CONFIG = {
    "metal_enabled": metal_enabled,
    "compute_units": "all" if metal_enabled else "cpu",
    "memory_limit": "8G",
    "batch_size": 1,
    "precision": "float16" if metal_enabled else "float32"
}

# Medical LLM configuration with M3 optimization
MEDICAL_LLM_CONFIG = {
    "model_endpoint": os.getenv('MEDICAL_LLM_ENDPOINT'),
    "model_name": "phi_lora_3b_medical_healthcaremagic_gguf",
    "temperature": 0.7,
    "max_tokens": 2048,
    "m3_config": M3_CONFIG,
    "stream": True,  # Enable streaming for real-time responses
    "top_p": 0.9,   # Nucleus sampling for more focused medical responses
    "top_k": 40     # Limit token selection for more precise outputs
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up Healthcare Simulation API...")
    try:
        # Initialize database
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
        # Initialize M3 optimizations
        if os.getenv("M3_OPTIMIZER_ENABLED", "true").lower() == "true":
            logger.info("M3 optimizations enabled")
            os.environ["VECLIB_MAXIMUM_THREADS"] = "8"
            
        # Initialize Metal framework
        if os.getenv("METAL_FRAMEWORK_ENABLED", "true").lower() == "true":
            logger.info("Metal framework enabled")
            
        # Configure M3 optimization
        os.environ["METAL_DEVICE_WRITABLE"] = "1"
        os.environ["METAL_DEBUG_ERROR_MODE"] = "1"
        
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Healthcare Simulation API...")
    try:
        db.remove()
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Simulation API",
    description="Healthcare Simulation API powered by Ollama multi-model support",
    version="0.2.0",
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

@app.get("/health")
async def health_check():
    """Check the health status of the API and its components."""
    try:
        # Check database connection
        db_status = "up"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "down"
            
        # Check medical LLM status
        llm_status = "up"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{MEDICAL_LLM_CONFIG['model_endpoint']}/api/tags")
                if response.status_code != 200:
                    llm_status = "down"
        except Exception:
            llm_status = "down"
            
        return {
            "status": "healthy" if db_status == "up" and llm_status == "up" else "unhealthy",
            "components": {
                "api": "up",
                "database": db_status,
                "medical_llm": llm_status,
                "m3_optimization": "up" if os.getenv("M3_OPTIMIZER_ENABLED", "true").lower() == "true" else "down",
                "metal_framework": "up" if os.getenv("METAL_FRAMEWORK_ENABLED", "true").lower() == "true" else "down"
            },
            "performance": {
                "metal_enabled": os.getenv("METAL_FRAMEWORK_ENABLED", "true").lower() == "true",
                "compute_units": "all",
                "memory_limit": "8G",
                "precision": "float16"
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@app.post("/v1/healthcare/simulate", response_model=SimulationResponse)
async def simulate_healthcare_scenario(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key)
):
    """Process a healthcare simulation scenario."""
    try:
        return await healthcare_ops.simulate_scenario(request, background_tasks)
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}"
        )

@app.post("/v1/healthcare/validate", response_model=ValidationResponse)
async def validate_protocol(
    request: ValidationRequest,
    api_key: str = Security(verify_api_key)
) -> ValidationResponse:
    """Validate a healthcare protocol."""
    try:
        return await healthcare_ops.validate_protocol(request)
    except Exception as e:
        logger.error(f"Error in validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )

# Include routers
logger.info("Including healthcare router with prefix: /v1")
app.include_router(
    render_router,
    prefix="/v1"
)
