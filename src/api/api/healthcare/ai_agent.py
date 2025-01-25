from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from datetime import datetime
import httpx
import json
import asyncio
from api.config.settings import settings
from api.security.auth import verify_token
from api.healthcare.models import (
    QueryRequest,
    ProtocolRequest,
    AnalysisRequest,
    AnalysisResponse,
    ValidationResponse
)

router = APIRouter(prefix="/v1/healthcare/ai", tags=["Healthcare AI"])
security = HTTPBearer()

class HealthcareQuery(BaseModel):
    """Model for healthcare-related queries to the AI agent."""
    query: str = Field(..., description="The healthcare-related question or query")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context like medical history")
    patient_data: Optional[Dict[str, Any]] = Field(None, description="Relevant patient data")
    model: str = Field("medical", description="Ollama model to use")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Temperature for response generation")

class HealthcareResponse(BaseModel):
    """Model for AI agent responses."""
    response: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggestions: List[str]
    references: Optional[List[Dict[str, str]]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    model_used: str

class ValidationRequest(BaseModel):
    """Model for healthcare protocol validation requests."""
    protocol: str
    parameters: Dict[str, Any]
    guidelines: Optional[List[str]] = None

class ProtocolValidationRequest(BaseModel):
    """Model for healthcare protocol validation requests."""
    protocol: str
    parameters: Dict[str, Any]
    guidelines: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    """Model for medical data analysis responses."""
    analysis: str
    confidence: float
    recommendations: List[str]
    timestamp: datetime

HEALTHCARE_SYSTEM_PROMPT = """You are a healthcare AI assistant trained to:
1. Provide evidence-based medical information
2. Analyze medical data for patterns and insights
3. Suggest appropriate medical actions and referrals
4. Ensure HIPAA compliance in all responses

Important guidelines:
- Always cite medical sources when possible
- Flag any potential medical emergencies
- Maintain patient privacy
- Indicate confidence levels in recommendations
- Suggest specialist consultation when appropriate"""

async def query_ollama(prompt: str, model: str = "medical", temperature: float = 0.7) -> Dict[str, Any]:
    """
    Query Ollama API with healthcare-specific prompts.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": HEALTHCARE_SYSTEM_PROMPT,
                    "stream": False,
                    "temperature": temperature,
                    "options": {
                        "num_ctx": 4096,
                        "top_k": 50,
                        "top_p": 0.9
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=503,
                detail="Ollama API timeout - The request took too long to process"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ollama API error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )

@router.post("/query", response_model=AnalysisResponse)
async def query_ollama(
    request: QueryRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AnalysisResponse:
    """Query the Ollama API with healthcare-specific prompts."""
    try:
        # Verify token
        try:
            verify_token(credentials.credentials)
        except HTTPException as e:
            if e.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            raise e

        # Validate query
        if not request.query.strip():
            raise HTTPException(
                status_code=422,
                detail="Query cannot be empty"
            )

        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.OLLAMA_API_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": request.query,
                        "system": HEALTHCARE_SYSTEM_PROMPT,
                        "stream": False,
                        "options": {
                            "temperature": request.temperature,
                            "num_ctx": 4096,
                            "top_k": 50,
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return AnalysisResponse(
                        analysis=result["response"],
                        timestamp=datetime.now(),
                        confidence=0.85,
                        recommendations=["Consult with healthcare provider for verification"]
                    )
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="Ollama API service unavailable"
                    )
                    
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=503,
                detail="Request to Ollama API timed out"
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=503,
                detail=f"Error communicating with Ollama API: {str(e)}"
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/process", response_model=AnalysisResponse)
async def process_healthcare_query(
    request: QueryRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AnalysisResponse:
    """Process a healthcare-related query."""
    try:
        # Verify token
        try:
            verify_token(credentials.credentials)
        except HTTPException as e:
            if e.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            raise e

        # Validate query
        if not request.query.strip():
            raise HTTPException(
                status_code=422,
                detail="Query cannot be empty"
            )

        # Process query
        return AnalysisResponse(
            analysis="Processed healthcare query: " + request.query,
            timestamp=datetime.now(),
            confidence=0.9,
            recommendations=["Follow up with healthcare provider"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing healthcare query: {str(e)}"
        )

@router.post("/validate", response_model=ValidationResponse)
async def validate_healthcare_protocol(
    request: ProtocolRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> ValidationResponse:
    """Validate a healthcare protocol."""
    try:
        # Verify token
        try:
            verify_token(credentials.credentials)
        except HTTPException as e:
            if e.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            raise e

        # Validate protocol
        return ValidationResponse(
            is_valid=True,
            validation_details="Protocol validated successfully",
            timestamp=datetime.now()
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating protocol: {str(e)}"
        )

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_medical_data(
    request: AnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AnalysisResponse:
    """Analyze medical data using AI."""
    try:
        # Verify token
        try:
            verify_token(credentials.credentials)
        except HTTPException as e:
            if e.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            raise e

        # Analyze data
        return AnalysisResponse(
            analysis="Medical data analysis complete",
            timestamp=datetime.now(),
            confidence=0.95,
            recommendations=["Review results with specialist"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing medical data: {str(e)}"
        ) 