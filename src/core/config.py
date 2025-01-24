from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Security Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "development_secret_key")
    API_KEY: str = os.getenv("API_KEY", "development_api_key")
    CORS_ORIGINS: List[str] = ["*"]
    
    # Quantum Settings
    QUANTUM_ALGORITHM: str = "CRYSTALS-Kyber1024"
    KEY_ROTATION_HOURS: int = 24
    MAX_CONCURRENT_SESSIONS: int = 100
    
    # Metrics Settings
    METRICS_COLLECTION_INTERVAL: int = 60  # seconds
    
    # M3 Optimization Settings
    M3_ENABLED: bool = True
    GPU_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True 