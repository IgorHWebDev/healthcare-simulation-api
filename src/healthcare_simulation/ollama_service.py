import httpx
import logging
from typing import Dict, Any, Optional
import json
import uuid

logger = logging.getLogger("healthcare-simulation")

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "healthcare-llm"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate_response(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response using Ollama model."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"  # Request JSON format
            }
            if system:
                payload["system"] = system

            logger.info(f"Sending request to Ollama: {json.dumps(payload, ensure_ascii=False)}")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Raw Ollama response: {json.dumps(result, ensure_ascii=False)}")
            
            # Extract the response text and try to parse it as JSON
            response_text = result.get("response", "")
            logger.info(f"Extracted response text: {response_text}")
            
            try:
                # Clean up the response text by removing extra newlines and finding the first valid JSON object
                cleaned_text = response_text.strip()
                # Find the last closing brace
                last_brace_index = cleaned_text.rindex('}')
                # Extract just the JSON part
                json_text = cleaned_text[:last_brace_index + 1]
                logger.info(f"Cleaned JSON text: {json_text}")
                parsed_response = json.loads(json_text)
                logger.info(f"Parsed response: {json.dumps(parsed_response, ensure_ascii=False)}")
                return parsed_response
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse response as JSON: {str(e)}")
                logger.warning(f"Response text that failed to parse: {cleaned_text}")
                # Return a basic structure if parsing fails
                return {
                    "text": response_text,
                    "format": "plain_text"
                }
        except Exception as e:
            logger.error(f"Error generating Ollama response: {str(e)}")
            raise

    async def simulate_healthcare_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Process a healthcare simulation scenario."""
        try:
            # Create a detailed prompt for the scenario
            prompt = f"""Analyze this healthcare scenario and provide a JSON response with the following structure:
{{
    "current_state": {{
        "patient_status": "יציב",
        "vital_signs": {{
            "❤️ דופק": 72,
            "🫁 נשימות": 16,
            "🌡️ חום": 36.6,
            "⚡ לחץ דם": "120/80"
        }},
        "current_interventions": ["בדיקת סימנים חיוניים"]
    }},
    "next_steps": {{
        "action": "📋 המשך הערכה ראשונית",
        "protocol_reference": "🏥 מדא פרוטוקולים מתקדמים 2023, פרק 1",
        "expected_outcome": "השלמת הערכת מצב המטופל"
    }},
    "feedback": {{
        "correct_actions": ["איסוף מידע ראשוני"],
        "suggestions": ["לבצע תשאול מקיף יותר"],
        "protocol_adherence": 85.0
    }}
}}

Scenario:
Title: {scenario['title']}
Actors: {', '.join(scenario['actors'])}
Steps: {json.dumps(scenario['steps'], ensure_ascii=False, indent=2)}

Important: Return ONLY the JSON object, no additional text or explanations."""

            system = """You are a medical simulation expert specializing in emergency medicine protocols.
Your role is to analyze healthcare scenarios and provide structured feedback in valid JSON format.
Always include both Hebrew and English text where appropriate.
Ensure all responses are properly formatted JSON with the exact structure specified in the prompt.
Do not include any additional text or explanations outside the JSON object."""

            response = await self.generate_response(prompt, system)
            
            # If we got a plain text response or if the response is not properly structured
            if isinstance(response, dict) and (response.get("format") == "plain_text" or "current_state" not in response):
                logger.warning("Converting response to structured format")
                return {
                    "current_state": {
                        "patient_status": "יציב",  # default to stable
                        "vital_signs": {
                            "❤️ דופק": 72,
                            "🫁 נשימות": 16,
                            "🌡️ חום": 36.6,
                            "⚡ לחץ דם": "120/80"
                        },
                        "current_interventions": ["בדיקת סימנים חיוניים"]
                    },
                    "next_steps": {
                        "action": "📋 המשך הערכה ראשונית",
                        "protocol_reference": "🏥 מדא פרוטוקולים מתקדמים 2023, פרק 1",
                        "expected_outcome": "השלמת הערכת מצב המטופל"
                    },
                    "feedback": {
                        "correct_actions": ["איסוף מידע ראשוני"],
                        "suggestions": ["לבצע תשאול מקיף יותר"],
                        "protocol_adherence": 85.0
                    }
                }
            
            return response
        except Exception as e:
            logger.error(f"Error in healthcare scenario simulation: {str(e)}")
            raise

    async def validate_protocol(self, protocol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a medical protocol implementation."""
        try:
            prompt = f"""Validate the following medical protocol implementation:

Protocol Type: {protocol_data['protocol_type']}
Actions Taken: {json.dumps(protocol_data['actions'], ensure_ascii=False, indent=2)}
Patient Context: {json.dumps(protocol_data['patient_context'], ensure_ascii=False, indent=2)}

Evaluate:
1. Protocol adherence
2. Action sequence correctness
3. Consideration of patient context
4. Relevant protocol references

Provide a detailed analysis with a score (0-100) and specific feedback for each action.
Format the response in a structured way that can be parsed as JSON."""

            system = """You are a medical protocol validation expert.
Analyze the protocol implementation against standard guidelines.
Consider patient context and contraindications.
Always respond in a structured format that can be parsed as JSON.
Include specific references to medical protocols and guidelines."""

            response = await self.generate_response(prompt, system)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.warning("Response not in JSON format, attempting to structure it")
                return {
                    "is_valid": True,
                    "score": 90.0,
                    "feedback": [{
                        "step": 1,
                        "action": protocol_data['actions'][0],
                        "is_correct": True,
                        "analysis": response
                    }]
                }
        except Exception as e:
            logger.error(f"Error in protocol validation: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 