"""
Configuration settings for the healthcare simulation API.
Includes environment-specific settings and Ollama integration configuration.
"""

import os
from typing import Dict, Any

# Environment configuration
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Ollama configuration
OLLAMA_CONFIG = {
    "development": {
        "base_url": "http://localhost:11434",
        "default_model": "phi_lora_3b_medical_healthcaremagic_gguf",
        "timeout": 30,
        "max_tokens": 2048
    },
    "production": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "default_model": os.getenv("OLLAMA_DEFAULT_MODEL", "phi_lora_3b_medical_healthcaremagic_gguf"),
        "timeout": int(os.getenv("OLLAMA_TIMEOUT", "30")),
        "max_tokens": int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))
    }
}

# M3 optimization configuration
M3_CONFIG = {
    "development": {
        "metal_enabled": True,
        "metal_device": 0,
        "compute_units": "all",
        "memory_limit": "8G",
        "precision": "float16"
    },
    "production": {
        "metal_enabled": os.getenv("METAL_FRAMEWORK_ENABLED", "true").lower() == "true",
        "metal_device": int(os.getenv("METAL_DEVICE", "0")),
        "compute_units": os.getenv("METAL_COMPUTE_UNITS", "all"),
        "memory_limit": os.getenv("METAL_MEMORY_LIMIT", "8G"),
        "precision": os.getenv("METAL_PRECISION", "float16")
    }
}

# Database configuration
DATABASE_CONFIG = {
    "development": {
        "url": "sqlite:///./healthcare.db",
        "echo": True
    },
    "production": {
        "url": os.getenv("DATABASE_URL", "sqlite:///./healthcare.db"),
        "echo": False
    }
}

def get_config(config_type: str) -> Dict[str, Any]:
    """Get configuration based on environment."""
    configs = {
        "ollama": OLLAMA_CONFIG,
        "m3": M3_CONFIG,
        "database": DATABASE_CONFIG
    }
    
    if config_type not in configs:
        raise ValueError(f"Invalid config type: {config_type}")
        
    return configs[config_type][ENV]
