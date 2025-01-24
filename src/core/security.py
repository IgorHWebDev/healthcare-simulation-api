import jwt
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict

from core.config import Settings

logger = logging.getLogger("iqhis.security")
settings = Settings()

def create_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm="HS256"
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise

def validate_token(token: str) -> bool:
    """Validate a JWT token."""
    try:
        jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        return True
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return False
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return False

def validate_api_key(api_key: str) -> bool:
    """Validate an API key."""
    try:
        return api_key == settings.API_KEY
    except Exception as e:
        logger.error(f"API key validation error: {str(e)}")
        return False 