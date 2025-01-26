"""
Ollama integration endpoints for healthcare simulation API.
Provides direct access to local Ollama models for medical text generation and analysis.
Optimized for M3 silicon chip with Metal framework acceleration.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import json
from datetime import datetime
from .ollama_config import OllamaConfig

# Initialize Ollama configuration
ollama_config = OllamaConfig()
OLLAMA_BASE_URL = ollama_config.base_url

# Configure Ollama client
router = APIRouter(prefix="/v1/ollama", tags=["Ollama Integration"])

# Pydantic models for request/response
class OllamaModel(BaseModel):
    name: str
    size: int
    modified_at: datetime
    metadata: Dict[str, Any]

class GenerationOptions(BaseModel):
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    top_p: Optional[float] = Field(0.9, ge=0, le=1)
    top_k: Optional[int] = Field(40, ge=0)
    num_predict: Optional[int] = Field(100, ge=0)
    stop: Optional[List[str]] = []

class GenerateRequest(BaseModel):
    model: str
    prompt: str
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None
    options: Optional[GenerationOptions] = GenerationOptions()

class GenerateResponse(BaseModel):
    model: str
    response: str
    context: Optional[List[int]]
    metadata: Dict[str, Any]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    options: Optional[GenerationOptions] = GenerationOptions()

class ChatResponse(BaseModel):
    model: str
    message: ChatMessage
    metadata: Dict[str, Any]

class EmbeddingRequest(BaseModel):
    model: str
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]

# Endpoints
@router.get("/models", response_model=Dict[str, List[OllamaModel]])
async def list_models():
    """List all available Ollama models with M3 optimization status."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {"models": [
                    OllamaModel(
                        name=model["name"],
                        size=model.get("size", 0),
                        modified_at=datetime.fromisoformat(model.get("modified_at", datetime.now().isoformat())),
                        metadata={
                            **model.get("metadata", {}),
                            "m3_optimized": ollama_config.is_m3,
                            "metal_enabled": ollama_config.metal_enabled,
                            "optimal_params": ollama_config.optimize_model_params(model["name"])
                        }
                    ) for model in models
                ]}
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch models")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")

@router.post("/generate", response_model=GenerateResponse)
async def generate_response(request: GenerateRequest):
    """Generate medical text using Ollama model with M3 optimizations."""
    try:
        # Get optimal configuration for the model
        model_params = ollama_config.optimize_model_params(request.model)
        
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "system": request.system,
            "template": request.template,
            "context": request.context,
            "options": {
                **(request.options.dict(exclude_none=True) if request.options else {}),
                **model_params
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={k: v for k, v in payload.items() if v is not None}
            )
            
            if response.status_code == 200:
                result = response.json()
                return GenerateResponse(
                    model=request.model,
                    response=result.get("response", ""),
                    context=result.get("context"),
                    metadata={
                        "eval_count": result.get("eval_count"),
                        "eval_duration": result.get("eval_duration"),
                        "resource_usage": ollama_config.get_resource_usage()
                    }
                )
            raise HTTPException(status_code=response.status_code, detail="Generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Interactive medical chat using Ollama."""
    try:
        payload = {
            "model": request.model,
            "messages": [msg.dict() for msg in request.messages],
            "options": request.options.dict(exclude_none=True) if request.options else None
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={k: v for k, v in payload.items() if v is not None}
            )
            
            if response.status_code == 200:
                result = response.json()
                return ChatResponse(
                    model=request.model,
                    message=ChatMessage(
                        role="assistant",
                        content=result.get("message", {}).get("content", "")
                    ),
                    metadata={
                        "eval_count": result.get("eval_count"),
                        "eval_duration": result.get("eval_duration")
                    }
                )
            raise HTTPException(status_code=response.status_code, detail="Chat failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest):
    """Generate embeddings for medical texts using Ollama."""
    try:
        embeddings = []
        async with httpx.AsyncClient() as client:
            for text in request.texts:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": request.model, "prompt": text}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embeddings.append(result.get("embedding", []))
                else:
                    raise HTTPException(status_code=response.status_code, detail="Embedding generation failed")
                
        return EmbeddingResponse(embeddings=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

# Health check for Ollama service
@router.get("/health")
async def health_check():
    """Check Ollama service health with detailed resource monitoring."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            
            health_status = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "m3_status": {
                    "is_m3": ollama_config.is_m3,
                    "metal_enabled": ollama_config.metal_enabled
                },
                "resource_usage": ollama_config.get_resource_usage()
            }
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                health_status["models"] = {
                    model["name"]: ollama_config.get_model_info(model["name"])
                    for model in models
                }
                
            return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "resource_usage": ollama_config.get_resource_usage()
        }
