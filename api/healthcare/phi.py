from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Security, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import json

from api.healthcare.models import (
    PHIData,
    PHIResponse,
    PHIRequest,
    AuditQuery,
    ErrorResponse,
    AuditLogEntry
)
from api.security.quantum import QuantumEncryption
from api.utils.audit import AuditLogger
from api.utils.json import json_dumps
from api.security.auth import verify_token, security
from api.models import AuditLogResponse
from api.config.settings import settings

router = APIRouter(prefix="/v1/healthcare/phi", tags=["PHI"])
security = HTTPBearer(auto_error=False)
quantum_encryption = QuantumEncryption()
audit_logger = AuditLogger()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    # TODO: Implement JWT validation and user extraction
    return {"id": "test_user", "role": "healthcare_provider"}

@router.post("/store", response_model=PHIResponse)
async def store_phi(
    request: PHIRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> PHIResponse:
    """Store PHI data with encryption."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verify token
        user_id = verify_token(credentials.credentials)
        
        # Create record ID with timestamp
        timestamp = datetime.now()
        record_id = f"PHI_{request.patient_id}_{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        # Encrypt data
        encrypted_data = quantum_encryption.encrypt(str(request.content))
        
        # Create PHI data object
        phi_data = PHIData(
            id=record_id,
            patient_id=request.patient_id,
            data_type=request.data_type,
            content=request.content,
            created_at=timestamp,
            encryption_key_id=quantum_encryption.current_key_id
        )
        
        # Log access
        await audit_logger.log_access(
            user_id=user_id,
            patient_id=request.patient_id,
            action="store",
            resource_type="phi",
            resource_id=record_id
        )
        
        return PHIResponse(
            id=record_id,
            patient_id=request.patient_id,
            data_type=request.data_type,
            content=request.content,
            encryption_key_id=quantum_encryption.current_key_id,
            created_at=phi_data.created_at
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing PHI data: {str(e)}"
        )

@router.get("/retrieve", response_model=PHIResponse)
async def retrieve_phi(
    patient_id: str,
    record_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> PHIResponse:
    """Retrieve PHI data by record ID."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verify token
        user_id = verify_token(credentials.credentials)
        
        # Validate record ID format
        if not record_id.startswith(f"PHI_{patient_id}_"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid record ID format"
            )
        
        # Mock data retrieval
        timestamp = datetime.now()
        mock_content = {"note": "Mock clinical note content"}
        
        # Create PHI data object
        phi_data = PHIData(
            id=record_id,
            patient_id=patient_id,
            data_type="clinical_note",
            content=mock_content,
            created_at=timestamp,
            encryption_key_id=quantum_encryption.current_key_id
        )
        
        # Log access
        await audit_logger.log_access(
            user_id=user_id,
            patient_id=patient_id,
            action="retrieve",
            resource_type="phi",
            resource_id=record_id
        )
        
        return PHIResponse(
            id=phi_data.id,
            patient_id=phi_data.patient_id,
            data_type=phi_data.data_type,
            content=phi_data.content,
            encryption_key_id=phi_data.encryption_key_id,
            created_at=phi_data.created_at
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PHI data: {str(e)}"
        )

@router.get("/audit", response_model=AuditLogResponse)
async def get_audit_logs(
    patient_id: Optional[str] = None,
    action: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AuditLogResponse:
    """Get audit logs with optional filtering."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verify token
        user_id = verify_token(credentials.credentials)
        
        # Get logs
        logs = await audit_logger.get_logs(
            patient_id=patient_id,
            action=action
        )
        
        return AuditLogResponse(logs=logs)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit logs: {str(e)}"
        ) 