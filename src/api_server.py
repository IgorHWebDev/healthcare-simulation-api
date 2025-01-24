from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import httpx
import os
import json
import logging
from uuid import uuid4
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthcare-api")

# Authentication settings
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "your-default-api-key")  # Set this in .env
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403,
        detail="Invalid API Key"
    )

# Initialize OpenAI client pointing to LM Studio
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "phi_lora_3b_medical_HealthcareMagic_gguf")
LM_STUDIO_BACKUP_MODEL = os.getenv("LM_STUDIO_BACKUP_MODEL", "Llama-3-2-1B-Instruct-Healthcare-Finetune")

lm_studio_client = OpenAI(
    base_url=os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1"),
    api_key="not-needed"
)

# Render API configuration
RENDER_API_URL = "https://healthcare-simulation-api.onrender.com"
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")

# CORS configuration
origins = [
    "https://healthcare-simulation-api.onrender.com",
    "https://chat.openai.com"  # Allow ChatGPT to make requests
]

app = FastAPI(
    title="Healthcare Simulation API",
    description="Interactive medical scenario simulation and validation API with both cloud and local LLM support",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    root_path="https://healthcare-simulation-api.onrender.com"  # Set the root path
)

# Configure CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Specify allowed methods
    allow_headers=["*"],
    expose_headers=["X-API-Key"]
)

# Models
class SimulationRequest(BaseModel):
    message: str
    language: str = "en"
    use_local_model: bool = False  # Flag to choose between Render API and local model

class SimulationResponse(BaseModel):
    scenario_id: str
    response: str
    next_steps: List[str]
    vital_signs: Optional[Dict[str, str]] = None
    model_used: str = "render-api"  # Indicates which model was used

class ValidationRequest(BaseModel):
    action: str
    protocol: str
    use_local_model: bool = False  # Flag to choose between Render API and local model

class ValidationResponse(BaseModel):
    is_valid: bool
    feedback: str
    score: float
    references: Optional[List[Dict[str, str]]] = None
    model_used: str = "render-api"  # Indicates which model was used

async def query_render_api(endpoint: str, data: dict) -> dict:
    """Query the Render API endpoint."""
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
            "X-RapidAPI-Key": RENDER_API_KEY
        }
        response = await client.post(
            f"{RENDER_API_URL}/{endpoint}",
            headers=headers,
            json=data
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Render API request failed")
        return response.json()

async def query_local_llm(prompt: str) -> str:
    """Query the local LM Studio model."""
    try:
        # Add logging for debugging
        logger.info(f"Querying LM Studio at {os.getenv('LM_STUDIO_URL')}")
        logger.info(f"Using model: {LM_STUDIO_MODEL}")
        
        # Prepare the system prompt for healthcare
        system_prompt = """You are an advanced medical simulation expert with deep knowledge of:
        - Emergency medical procedures
        - Clinical protocols (ACLS, BLS, PALS)
        - Vital signs interpretation
        - Medical decision making
        - Healthcare team coordination
        
        Provide detailed, structured responses that include:
        1. Clear assessment of the situation
        2. Vital signs when relevant
        3. Prioritized action steps
        4. Clinical reasoning for recommendations
        """
        
        completion = lm_studio_client.chat.completions.create(
            model=LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=0.95,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        response = completion.choices[0].message.content
        
        # Log response if verbose logging is enabled
        if os.getenv("VERBOSE_LOGGING", "false").lower() == "true":
            logger.info(f"LLM Response: {response}")
            
        return response
        
    except Exception as primary_error:
        logger.error(f"Error with primary model: {str(primary_error)}")
        try:
            logger.info(f"Attempting fallback to backup model: {LM_STUDIO_BACKUP_MODEL}")
            # Fallback to backup model
            completion = lm_studio_client.chat.completions.create(
                model=LM_STUDIO_BACKUP_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return completion.choices[0].message.content
        except Exception as backup_error:
            logger.error(f"Error with backup model: {str(backup_error)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Model generation failed",
                    "primary_error": str(primary_error),
                    "backup_error": str(backup_error)
                }
            )

def parse_vital_signs(text: str) -> Dict[str, str]:
    """Extract vital signs from the response text with improved parsing."""
    vital_signs = {}
    vital_patterns = {
        "heart_rate": (r"heart rate[:\s]+(\d+(?:\.\d+)?)", "❤️"),
        "blood_pressure": (r"blood pressure[:\s]+(\d+/\d+)", "⚡"),
        "temperature": (r"temperature[:\s]+(\d+(?:\.\d+)?)", "🌡️"),
        "respiratory_rate": (r"respiratory rate[:\s]+(\d+(?:\.\d+)?)", "🫁"),
        "oxygen_saturation": (r"(?:oxygen saturation|spo2|o2 sat)[:\s]+(\d+(?:\.\d+)?)", "💨"),
        "consciousness": (r"(?:consciousness|gcs)[:\s]+([A-Za-z0-9/]+)", "🧠")
    }
    
    text_lower = text.lower()
    for key, (pattern, emoji) in vital_patterns.items():
        import re
        match = re.search(pattern, text_lower)
        if match:
            vital_signs[key] = f"{emoji} {match.group(1)}"
    
    return vital_signs

def extract_next_steps(text: str) -> List[str]:
    """Extract next steps from the response text with improved parsing."""
    steps = []
    lines = text.split("\n")
    
    # Common medical action indicators
    indicators = [
        "-", "*", "•", "→", "▶",
        *[f"{i}." for i in range(1, 11)],
        *[f"Step {i}:" for i in range(1, 11)],
        "Assess", "Check", "Monitor", "Administer", "Perform"
    ]
    
    in_steps_section = False
    for line in lines:
        line = line.strip()
        
        # Detect steps section
        if any(keyword in line.lower() for keyword in ["next steps:", "action items:", "recommended actions:", "interventions:"]):
            in_steps_section = True
            continue
            
        if in_steps_section and line:
            # Check if line starts with any indicator
            if any(line.startswith(ind) for ind in indicators):
                # Clean up the step text
                step = line
                for ind in indicators:
                    step = step.replace(ind, "").strip()
                if step:
                    steps.append(step)
            # Or if it looks like a medical action
            elif any(action in line.lower() for action in ["assess", "check", "monitor", "administer", "perform", "evaluate", "provide"]):
                steps.append(line)
                
    # Fallback if no steps found
    if not steps:
        steps = [
            "Assess patient condition",
            "Check vital signs",
            "Monitor patient status",
            "Follow appropriate medical protocols",
            "Document findings and interventions"
        ]
    
    return steps

@app.post("/simulate", response_model=SimulationResponse)
async def simulate_scenario(
    request: SimulationRequest,
    api_key: str = Depends(get_api_key)
):
    """Process an interactive medical simulation scenario with real-time feedback."""
    try:
        if not request.use_local_model:
            # Use Render API
            response = await query_render_api("simulate", request.dict(exclude={"use_local_model"}))
            response["model_used"] = "render-api"
            return SimulationResponse(**response)
        
        # Use local LM Studio model
        prompt = f"""You are a medical simulation expert. Given the following scenario, provide a detailed response including vital signs and next steps.
        
        Scenario: {request.message}
        
        Provide your response in the following format:
        1. Current situation and vital signs
        2. List of recommended next steps
        """
        
        response_text = await query_local_llm(prompt)
        vital_signs = parse_vital_signs(response_text)
        next_steps = extract_next_steps(response_text)
        
        return SimulationResponse(
            scenario_id=str(uuid4()),
            response=response_text,
            next_steps=next_steps,
            vital_signs=vital_signs,
            model_used="lm-studio-local"
        )
    except Exception as e:
        logger.error(f"Error in simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate", response_model=ValidationResponse)
async def validate_action(
    request: ValidationRequest,
    api_key: str = Depends(get_api_key)
):
    """Validate healthcare decisions against standard protocols."""
    try:
        if not request.use_local_model:
            # Use Render API
            response = await query_render_api("validate", request.dict(exclude={"use_local_model"}))
            response["model_used"] = "render-api"
            return ValidationResponse(**response)
        
        # Use local LM Studio model
        prompt = f"""You are a medical protocol validation expert. Validate the following action against {request.protocol} protocol:
        
        Action: {request.action}
        Protocol: {request.protocol}
        
        Provide your response in the following format:
        1. Validity assessment
        2. Detailed feedback
        3. Protocol adherence score (0-100)
        4. Relevant protocol references
        """
        
        response_text = await query_local_llm(prompt)
        is_valid = "correct" in response_text.lower() or "valid" in response_text.lower()
        score = 85.0 if is_valid else 45.0
        
        return ValidationResponse(
            is_valid=is_valid,
            feedback=response_text,
            score=score,
            references=[{
                "protocol": request.protocol,
                "section": "General Guidelines",
                "details": "Based on current medical protocols"
            }],
            model_used="lm-studio-local"
        )
    except Exception as e:
        logger.error(f"Error in validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running."""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 