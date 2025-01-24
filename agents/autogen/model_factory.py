"""
Model Factory for IQHIS AutoGen Integration
Handles dynamic model switching and healthcare-specific model selection
"""

import yaml
from typing import Dict, List, Optional
from enum import Enum
import logging
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    BASE = "base"
    SPECIALIZED = "specialized"
    ADVANCED = "advanced"

class TaskType(Enum):
    MEDICAL_DIAGNOSIS = "medical_diagnosis"
    TREATMENT_PLANNING = "treatment_planning"
    DRUG_INTERACTION = "drug_interaction"
    GENERAL_QUERY = "general_query"
    SYSTEM_SUPPORT = "system_support"

@dataclass
class ModelConfig:
    name: str
    type: ModelType
    context_length: int
    temperature: float = 0.7
    provider: str = "ollama"

class ModelProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def validate_response(self, response: str) -> bool:
        pass

class OllamaProvider(ModelProvider):
    async def generate_response(self, prompt: str, **kwargs) -> str:
        # Implement Ollama-specific generation logic
        pass

    async def validate_response(self, response: str) -> bool:
        # Implement Ollama-specific validation
        pass

class OpenAIProvider(ModelProvider):
    async def generate_response(self, prompt: str, **kwargs) -> str:
        # Implement OpenAI-specific generation logic
        pass

    async def validate_response(self, response: str) -> bool:
        # Implement OpenAI-specific validation
        pass

class ModelFactory:
    def __init__(self, config_path: str = "config/autogen.yaml"):
        self.config = self._load_config(config_path)
        self.providers: Dict[str, ModelProvider] = {
            "ollama": OllamaProvider(),
            "openai": OpenAIProvider()
        }
        self.current_model: Optional[ModelConfig] = None
        self.fallback_model: Optional[ModelConfig] = None

    def _load_config(self, config_path: str) -> Dict:
        """Load and validate configuration file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Successfully loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def select_model(self, 
                    task_type: TaskType,
                    medical_specialty: Optional[str] = None,
                    urgency_level: int = 1,
                    data_sensitivity: int = 1) -> ModelConfig:
        """
        Select appropriate model based on task requirements and constraints
        """
        try:
            # Apply selection criteria from config
            criteria = self.config['model_factory']['selection_criteria']
            
            if task_type in [TaskType.MEDICAL_DIAGNOSIS, TaskType.TREATMENT_PLANNING]:
                # Use healthcare-specific models for medical tasks
                model_config = self._get_healthcare_model(medical_specialty, urgency_level)
            else:
                # Use general-purpose models for other tasks
                model_config = self._get_general_model(task_type)

            self.current_model = model_config
            self.fallback_model = self._get_fallback_model(model_config)
            
            logger.info(f"Selected model: {model_config.name} for task: {task_type}")
            return model_config

        except Exception as e:
            logger.error(f"Error selecting model: {e}")
            raise

    def _get_healthcare_model(self, specialty: Optional[str], urgency: int) -> ModelConfig:
        """Select appropriate healthcare model based on specialty and urgency"""
        models = self.config['models']['local']['healthcare']['models']
        
        # Select specialized model for high urgency or specific specialty
        if urgency > 2 or specialty in self.config['healthcare']['specialties']:
            for model in models:
                if model['type'] == 'specialized':
                    return ModelConfig(**model)
        
        # Default to base healthcare model
        return ModelConfig(**next(m for m in models if m['type'] == 'base'))

    def _get_general_model(self, task_type: TaskType) -> ModelConfig:
        """Select appropriate general-purpose model"""
        models = self.config['models']['local']['general']['models']
        return ModelConfig(**models[0])  # Currently using first available model

    def _get_fallback_model(self, primary_model: ModelConfig) -> ModelConfig:
        """Select appropriate fallback model"""
        remote_models = self.config['models']['remote']['models']
        return ModelConfig(**remote_models[0])  # Using GPT-4 as fallback

    async def handle_model_failure(self, error_type: str) -> bool:
        """
        Handle model failures according to fallback rules
        Returns: True if fallback successful, False otherwise
        """
        try:
            fallback_rules = self.config['model_factory']['fallback_rules']
            
            for rule in fallback_rules:
                if rule['condition'] == error_type:
                    if rule['action'] == 'switch_to_fallback' and self.fallback_model:
                        self.current_model = self.fallback_model
                        logger.info(f"Switched to fallback model: {self.fallback_model.name}")
                        return True
                    elif rule['action'] == 'human_review':
                        logger.warning("Escalating to human review")
                        return False

            logger.error(f"No fallback rule found for error: {error_type}")
            return False

        except Exception as e:
            logger.error(f"Error handling model failure: {e}")
            return False

    async def validate_model_output(self, 
                                  response: str,
                                  task_type: TaskType,
                                  medical_specialty: Optional[str] = None) -> bool:
        """
        Validate model output based on task type and domain requirements
        """
        try:
            # Get validation settings from config
            validation_config = self.config['healthcare']['validation']
            
            # Basic validation
            if not response:
                return False

            # Healthcare-specific validation
            if task_type in [TaskType.MEDICAL_DIAGNOSIS, TaskType.TREATMENT_PLANNING]:
                confidence_threshold = validation_config['confidence_threshold']
                
                # Implement domain-specific validation logic here
                # For now, returning True as placeholder
                return True

            # General validation for non-healthcare tasks
            return True

        except Exception as e:
            logger.error(f"Error validating model output: {e}")
            return False

    def get_model_metrics(self) -> Dict:
        """
        Get current model performance metrics
        """
        return {
            "current_model": self.current_model.name if self.current_model else None,
            "fallback_model": self.fallback_model.name if self.fallback_model else None,
            "provider": self.current_model.provider if self.current_model else None,
            # Add additional metrics as needed
        } 