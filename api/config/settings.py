from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from datetime import timedelta

class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_VERSION: str = "0.1.0"
    API_KEY: str = "test-api-key"
    DOMAIN: str = "api.iqhis.com"
    STAGING_DOMAIN: str = "staging.api.iqhis.com"
    ADMIN_EMAIL: str = "admin@iqhis.com"
    
    # Security Settings
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_PRIVATE_KEY: str = "/etc/nginx/security/jwt_private.key"
    JWT_PUBLIC_KEY: str = "/etc/nginx/security/jwt_public.key"
    
    # Quantum Settings
    QUANTUM_KEY_ROTATION_HOURS: int = 24
    QUANTUM_ENCRYPTION_ALGORITHM: str = "KYBER1024"
    
    # Monitoring Settings
    METRICS_ENABLED: bool = True
    METRICS_INTERVAL_SECONDS: int = 60
    PROMETHEUS_USER: str = "prometheus"
    PROMETHEUS_PASSWORD: str = "secure_password_here"
    METRICS_CLIENT_ID: str = "metrics_client"
    METRICS_CLIENT_SECRET: str = "metrics_secret"
    
    # Client Settings
    CLIENT_ID: str = "iqhis_client"
    CLIENT_SECRET: str = "iqhis_secret"
    
    # Port Settings
    NGINX_PORT: str = "8080"
    API_PORT: str = "8000"
    PROMETHEUS_PORT: str = "9090"
    NODE_EXPORTER_PORT: str = "9100"
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    AUDIT_LOG_PATH: Optional[str] = None
    
    # Ollama Configuration
    OLLAMA_API_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TIMEOUT: int = 30
    
    # Quantum Encryption Configuration
    QUANTUM_KEY_LENGTH: int = 256
    
    # Audit Configuration
    AUDIT_LOG_DIR: str = "logs/audit"
    AUDIT_RETENTION_DAYS: int = 90
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

# Create settings instance
settings = Settings() 