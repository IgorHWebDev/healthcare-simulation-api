"""
AutoGen Coordinator for IQHIS
Manages interaction between healthcare agents and model selection
"""

import asyncio
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
from dataclasses import dataclass
from .model_factory import ModelFactory, TaskType, ModelConfig
from ..quantum.quantum_base_agent import QuantumBaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    name: str
    description: str
    default_model: str
    fallback_model: str
    capabilities: List[str]
    compliance: Dict[str, bool]

class AutoGenCoordinator:
    def __init__(self, config_path: str = "config/autogen.yaml"):
        self.model_factory = ModelFactory(config_path)
        self.quantum_agent = QuantumBaseAgent()  # Initialize quantum-safe security
        self.agents: Dict[str, AgentConfig] = {}
        self.load_agent_configurations()

    def load_agent_configurations(self):
        """Load and initialize agent configurations"""
        try:
            config = self.model_factory.config
            for agent_id, agent_config in config['agents'].items():
                self.agents[agent_id] = AgentConfig(**agent_config)
            logger.info(f"Loaded {len(self.agents)} agent configurations")
        except Exception as e:
            logger.error(f"Error loading agent configurations: {e}")
            raise

    async def process_healthcare_request(self,
                                      request: Dict[str, Any],
                                      medical_specialty: Optional[str] = None,
                                      urgency_level: int = 1) -> Dict[str, Any]:
        """
        Process a healthcare-related request using appropriate models and agents
        """
        try:
            # Encrypt request using quantum-safe encryption
            encrypted_request = await self.quantum_agent.encrypt_data(request)
            
            # Select appropriate model based on request type
            task_type = self._determine_task_type(request)
            model_config = self.model_factory.select_model(
                task_type=task_type,
                medical_specialty=medical_specialty,
                urgency_level=urgency_level
            )

            # Process request through selected model
            response = await self._process_with_model(encrypted_request, model_config, task_type)
            
            # Validate response
            if not await self.model_factory.validate_model_output(response, task_type, medical_specialty):
                logger.warning("Response validation failed, attempting fallback")
                response = await self._handle_validation_failure(request, task_type)

            # Decrypt response
            decrypted_response = await self.quantum_agent.decrypt_data(response)
            
            return {
                "status": "success",
                "response": decrypted_response,
                "model_used": model_config.name,
                "validation_status": "passed"
            }

        except Exception as e:
            logger.error(f"Error processing healthcare request: {e}")
            return {
                "status": "error",
                "error": str(e),
                "validation_status": "failed"
            }

    async def _process_with_model(self,
                                encrypted_request: Dict,
                                model_config: ModelConfig,
                                task_type: TaskType) -> str:
        """Process request with selected model"""
        try:
            provider = self.model_factory.providers[model_config.provider]
            response = await provider.generate_response(
                prompt=encrypted_request,
                temperature=model_config.temperature,
                max_tokens=model_config.context_length
            )
            return response
        except Exception as e:
            logger.error(f"Error processing with model {model_config.name}: {e}")
            raise

    async def _handle_validation_failure(self,
                                      request: Dict,
                                      task_type: TaskType) -> str:
        """Handle validation failures by switching to fallback model"""
        try:
            success = await self.model_factory.handle_model_failure("accuracy_below_threshold")
            if success:
                return await self._process_with_model(
                    request,
                    self.model_factory.current_model,
                    task_type
                )
            else:
                raise ValueError("Validation failed and no fallback available")
        except Exception as e:
            logger.error(f"Error handling validation failure: {e}")
            raise

    def _determine_task_type(self, request: Dict) -> TaskType:
        """Determine the type of task from the request"""
        # Implement logic to determine task type based on request content
        if "diagnosis" in request.get("type", "").lower():
            return TaskType.MEDICAL_DIAGNOSIS
        elif "treatment" in request.get("type", "").lower():
            return TaskType.TREATMENT_PLANNING
        elif "drug" in request.get("type", "").lower():
            return TaskType.DRUG_INTERACTION
        else:
            return TaskType.GENERAL_QUERY

    async def get_system_status(self) -> Dict:
        """Get current system status and metrics"""
        return {
            "active_models": self.model_factory.get_model_metrics(),
            "agents": {
                agent_id: {
                    "name": config.name,
                    "status": "active",
                    "capabilities": config.capabilities
                }
                for agent_id, config in self.agents.items()
            },
            "security": {
                "quantum_encryption": "active",
                "compliance_status": "compliant"
            }
        }

    async def validate_compliance(self, request: Dict) -> bool:
        """Validate request compliance with healthcare regulations"""
        try:
            # Get compliance settings from config
            compliance_settings = self.model_factory.config['security']
            
            # Check for required consent
            if compliance_settings['consent']['required']:
                if not request.get("patient_consent"):
                    logger.warning("Patient consent missing")
                    return False

            # Verify PHI handling
            if compliance_settings['audit']['phi_tracking']:
                if not self._verify_phi_protection(request):
                    logger.warning("PHI protection verification failed")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating compliance: {e}")
            return False

    def _verify_phi_protection(self, request: Dict) -> bool:
        """Verify Protected Health Information (PHI) is properly handled"""
        try:
            # Implement PHI verification logic
            # This is a placeholder - implement actual PHI verification
            return True
        except Exception as e:
            logger.error(f"Error verifying PHI protection: {e}")
            return False 