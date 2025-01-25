"""
AutoGen Integration for Healthcare Database Operations.
"""
from typing import Dict, List, Optional, Any
import autogen
from pathlib import Path
import logging

from .base import DatabaseInterface, HealthcareDataModel
from ..utils.m3_optimization import M3Optimizer

logger = logging.getLogger(__name__)

class AutoGenDBAdapter:
    """Adapter for AutoGen integration with healthcare database."""
    
    def __init__(self, db_interface: DatabaseInterface, config_path: str):
        """Initialize AutoGen adapter with database interface."""
        self.db = db_interface
        self.config = self._load_config(config_path)
        self.m3_optimizer = M3Optimizer()
        self._setup_agents()

    def _load_config(self, config_path: str) -> Dict:
        """Load AutoGen configuration."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        return autogen.config_load_yaml(config_file)

    def _setup_agents(self):
        """Initialize AutoGen agents for healthcare tasks."""
        # Clinical Analysis Agent
        self.clinical_agent = autogen.AssistantAgent(
            name="clinical_analyst",
            system_message="Healthcare clinical data analyst specialized in MIMIC-4 data interpretation.",
            llm_config=self.config.get("clinical_config", {})
        )

        # Diagnostic Support Agent
        self.diagnostic_agent = autogen.AssistantAgent(
            name="diagnostic_support",
            system_message="Medical diagnostic support specialist with MIMIC-4 integration.",
            llm_config=self.config.get("diagnostic_config", {})
        )

        # Research Assistant Agent
        self.research_agent = autogen.AssistantAgent(
            name="research_assistant",
            system_message="Healthcare research assistant for data analysis and study design.",
            llm_config=self.config.get("research_config", {})
        )

    async def analyze_patient_data(self, patient_id: str) -> Dict:
        """Analyze patient data using AutoGen agents."""
        try:
            # Fetch patient data with M3 optimization
            with self.m3_optimizer.optimize_processing():
                patient_data = await self.db.get_patient_data(patient_id)
            
            # Process with Clinical Agent
            clinical_analysis = await self._process_with_agent(
                self.clinical_agent,
                "analyze_clinical_data",
                patient_data
            )
            
            # Process with Diagnostic Agent
            diagnostic_analysis = await self._process_with_agent(
                self.diagnostic_agent,
                "analyze_diagnostics",
                patient_data
            )
            
            return {
                "clinical_analysis": clinical_analysis,
                "diagnostic_analysis": diagnostic_analysis
            }
        except Exception as e:
            logger.error(f"Patient data analysis failed: {e}")
            return {}

    async def generate_research_query(self, research_params: Dict) -> str:
        """Generate optimized research query using AutoGen."""
        try:
            # Process with Research Agent
            query = await self._process_with_agent(
                self.research_agent,
                "generate_research_query",
                research_params
            )
            
            return query
        except Exception as e:
            logger.error(f"Research query generation failed: {e}")
            return ""

    async def _process_with_agent(self, agent: autogen.AssistantAgent,
                                task: str, data: Dict) -> Any:
        """Process data with specified AutoGen agent."""
        try:
            # Optimize processing with M3
            with self.m3_optimizer.optimize_agent_processing():
                response = await agent.achat(
                    message={"task": task, "data": data},
                    max_turns=3
                )
            return response
        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return None

    async def validate_clinical_data(self, data: Dict) -> bool:
        """Validate clinical data using AutoGen agents."""
        try:
            validation_result = await self._process_with_agent(
                self.clinical_agent,
                "validate_clinical_data",
                data
            )
            return validation_result.get("is_valid", False)
        except Exception as e:
            logger.error(f"Clinical data validation failed: {e}")
            return False
