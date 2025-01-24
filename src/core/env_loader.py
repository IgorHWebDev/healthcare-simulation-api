"""
Environment Variable Loader

This module provides secure loading of environment variables with validation
and encryption support for sensitive data.
"""

import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import logging
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class EnvironmentLoader:
    """Secure environment variable loader with encryption support."""
    
    def __init__(self, env_path: Optional[str] = None):
        """Initialize the environment loader.
        
        Args:
            env_path: Optional path to .env file
        """
        self.env_path = env_path or '.env'
        self._load_environment()
        self._validate_required_vars()
        
    def _load_environment(self) -> None:
        """Load environment variables from file."""
        env_path = Path(self.env_path)
        if not env_path.exists():
            logger.warning(f"Environment file not found: {self.env_path}")
            return
            
        load_dotenv(self.env_path)
        logger.info(f"Loaded environment from: {self.env_path}")
        
    def _validate_required_vars(self) -> None:
        """Validate that all required variables are present."""
        required_vars = [
            'ENVIRONMENT',
            'PORT',
            'RENDER_API_KEY',
            'API_KEY_HEADER'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get an environment variable with optional default.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
        
    def get_encrypted(self, key: str, encryption_key: bytes) -> Optional[str]:
        """Get and decrypt an encrypted environment variable.
        
        Args:
            key: Environment variable name
            encryption_key: Key for decryption
            
        Returns:
            Decrypted value or None if not found
        """
        encrypted_value = self.get(key)
        if not encrypted_value:
            return None
            
        f = Fernet(encryption_key)
        return f.decrypt(encrypted_value.encode()).decode()
        
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Boolean value of environment variable
        """
        value = self.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
        
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.get('ENVIRONMENT') == 'production'
        
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.get('ENVIRONMENT') == 'development'
        
    def get_all(self) -> Dict[str, str]:
        """Get all environment variables as dictionary.
        
        Returns:
            Dictionary of all environment variables
        """
        return dict(os.environ) 