import aiohttp
import json
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def generate_response(self, 
                              prompt: str, 
                              model: str = "llama2", 
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7) -> Dict:
        """
        Generate a response using Ollama API
        """
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "model": model,
                        "metadata": {
                            "total_duration": result.get("total_duration", 0),
                            "load_duration": result.get("load_duration", 0),
                            "prompt_eval_count": result.get("prompt_eval_count", 0),
                            "eval_count": result.get("eval_count", 0)
                        }
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Error from Ollama API: {error_text}")
                    return {
                        "success": False,
                        "error": f"API Error: {response.status} - {error_text}"
                    }

        except Exception as e:
            logger.error(f"Exception in generate_response: {str(e)}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }

    async def list_models(self) -> Dict:
        """
        List available models from Ollama
        """
        try:
            url = f"{self.base_url}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "models": [model["name"] for model in result.get("models", [])]
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API Error: {response.status} - {error_text}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }

    async def health_check(self) -> Dict:
        """
        Check if Ollama service is healthy
        """
        try:
            url = f"{self.base_url}/api/tags"
            async with self.session.get(url) as response:
                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "message": "Ollama service is healthy" if response.status == 200 else "Ollama service is not responding"
                }
        except Exception as e:
            return {
                "success": False,
                "status": 500,
                "message": f"Error connecting to Ollama: {str(e)}"
            }
