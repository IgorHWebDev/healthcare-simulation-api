from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from api.healthcare.phi import router as phi_router
from api.healthcare.ai_agent import router as ai_router
from api.healthcare.models import (
    EncryptionRequest,
    EncryptionResponse,
    MetricsResponse,
    HealthResponse
)
from api.security.quantum import QuantumEncryption
from api.security.auth import verify_token
from api.utils.audit import AuditLogger
from api.config.settings import settings

app = FastAPI(
    title="Integrated Quantum-Resistant Healthcare Information System API with AI Agent",
    description="A secure healthcare information system with quantum-resistant encryption and AI capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
quantum_encryption = QuantumEncryption()
audit_logger = AuditLogger()
security = HTTPBearer()

# Include routers
app.include_router(phi_router)
app.include_router(ai_router)

@app.get("/")
async def root():
    """
    Root endpoint returning API information.
    """
    return {"message": "Healthcare Framework API"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }

@app.post("/v1/encrypt", response_model=EncryptionResponse)
async def encrypt_data(
    request: EncryptionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Encrypt data using quantum-resistant encryption."""
    try:
        verify_token(credentials.credentials)
    except HTTPException as e:
        if e.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        raise e

    try:
        encrypted = quantum_encryption.encrypt(request.data)
        return EncryptionResponse(
            encrypted_data=encrypted,
            key_id=quantum_encryption.current_key_id,
            expiry=datetime.now() + timedelta(hours=24)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encrypting data: {str(e)}"
        )

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(api_key: str = Header(None, alias="X-API-Key")):
    """Get system metrics."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is required"
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return MetricsResponse(
        requests_total=100,
        errors_total=5,
        latency_ms=150.5
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer"
        },
        "ApiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Apply security requirement to all operations
    openapi_schema["security"] = [{"Bearer": []}, {"ApiKey": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi 