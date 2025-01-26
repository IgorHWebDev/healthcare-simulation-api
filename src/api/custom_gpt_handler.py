"""
Custom GPT handler for integrating with Ollama healthcare model endpoints.
Provides seamless interaction between custom GPT and our healthcare simulation API.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import httpx
import json
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
from .ollama_config import OllamaConfig
from .healthcare.models import VitalSigns, PatientStatus

router = APIRouter(prefix="/v1/custom-gpt", tags=["Custom GPT Integration"])

# Initialize Ollama configuration with M3 optimizations
ollama_config = OllamaConfig()

class CustomGPTRequest(BaseModel):
    """Custom GPT request model."""
    query: str = Field(..., description="User query or command")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    patient_data: Optional[Dict[str, Any]] = Field(None, description="Patient-specific data")
    model_name: str = Field(default="phi_lora_3b_medical_healthcaremagic_gguf", description="Ollama model name")

class CustomGPTResponse(BaseModel):
    """Custom GPT response model."""
    response: str = Field(..., description="Generated response")
    recommendations: List[str] = Field(default_list=[], description="Medical recommendations")
    vital_signs: Optional[Dict[str, Any]] = Field(None, description="Updated vital signs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

async def get_model_capabilities() -> Dict[str, Any]:
    """Get available model capabilities and endpoints."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_config.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "available_models": [
                        {
                            "name": model["name"],
                            "capabilities": [
                                "medical_diagnosis",
                                "treatment_recommendations",
                                "vital_signs_analysis",
                                "emergency_protocols"
                            ],
                            "optimized_for_m3": ollama_config.is_m3,
                            "metal_enabled": ollama_config.metal_enabled
                        }
                        for model in models
                        if "medical" in model["name"].lower()
                    ],
                    "endpoints": {
                        "generate": "/v1/ollama/generate",
                        "chat": "/v1/ollama/chat",
                        "simulate": "/v1/healthcare/simulate",
                        "validate": "/v1/healthcare/validate"
                    }
                }
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch model capabilities")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model capabilities: {str(e)}")

@router.post("/process", response_model=CustomGPTResponse)
async def process_gpt_request(request: CustomGPTRequest):
    """Process custom GPT request using Ollama healthcare model."""
    try:
        # Get model capabilities
        capabilities = await get_model_capabilities()
        
        # Prepare optimized model parameters
        model_params = ollama_config.optimize_model_params(request.model_name)
        
        # Prepare chat context
        chat_messages = [
            {
                "role": "system",
                "content": "You are a medical AI assistant with access to the following capabilities: "
                          f"{json.dumps(capabilities, indent=2)}\n"
                          "You can process medical queries, provide diagnoses, and recommend treatments."
            },
            {
                "role": "user",
                "content": request.query
            }
        ]
        
        # Add patient context if available
        if request.patient_data:
            chat_messages.append({
                "role": "system",
                "content": f"Patient Data: {json.dumps(request.patient_data, indent=2)}"
            })
        
        # Make request to Ollama chat endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_config.base_url}/v1/ollama/chat",
                json={
                    "model": request.model_name,
                    "messages": chat_messages,
                    "options": {
                        **model_params,
                        "temperature": 0.7,  # Balanced between creativity and accuracy
                        "top_p": 0.9  # High-quality medical responses
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract medical recommendations and vital signs
                medical_response = result["message"]["content"]
                recommendations = [
                    line.strip("- ") for line in medical_response.split("\n")
                    if line.strip().startswith("- ")
                ]
                
                # Update vital signs if present in response
                vital_signs = None
                if request.patient_data and "vital_signs" in request.patient_data:
                    vital_signs = request.patient_data["vital_signs"]
                
                return CustomGPTResponse(
                    response=medical_response,
                    recommendations=recommendations,
                    vital_signs=vital_signs,
                    metadata={
                        "model": request.model_name,
                        "capabilities": capabilities["available_models"][0]["capabilities"],
                        "m3_optimized": ollama_config.is_m3,
                        "metal_enabled": ollama_config.metal_enabled,
                        "resource_usage": ollama_config.get_resource_usage()
                    }
                )
            
            raise HTTPException(status_code=response.status_code, detail="Failed to process request")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/capabilities")
async def get_capabilities():
    """Get available capabilities and endpoints."""
    return await get_model_capabilities()

@router.get("/health")
async def health_check():
    """Check custom GPT integration health."""
    try:
        capabilities = await get_model_capabilities()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "capabilities": capabilities,
            "m3_status": {
                "is_m3": ollama_config.is_m3,
                "metal_enabled": ollama_config.metal_enabled
            },
            "resource_usage": ollama_config.get_resource_usage()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
