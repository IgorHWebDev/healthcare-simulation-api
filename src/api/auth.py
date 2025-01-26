from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette import status
import os
import logging

logger = logging.getLogger(__name__)

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify the API key from the X-API-Key header."""
    logger.info(f"Verifying API key. Expected: {API_KEY}, Received: {api_key}")
    if not API_KEY:
        logger.error("API key not configured on server")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on server"
        )
    if api_key != API_KEY:
        logger.error(f"Invalid API key received: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key
