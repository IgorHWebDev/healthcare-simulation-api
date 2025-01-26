from typing import Dict, List, Optional
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomGPTHandler:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def create_custom_assistant(self, 
                                    name: str, 
                                    instructions: str, 
                                    tools: List[Dict] = None) -> Dict:
        """
        Create a custom GPT assistant
        """
        try:
            url = f"{self.base_url}/assistants"
            payload = {
                "name": name,
                "instructions": instructions,
                "model": "gpt-4-1106-preview",
                "tools": tools or [{"type": "code_interpreter"}]
            }

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "assistant_id": result.get("id"),
                        "created_at": datetime.fromtimestamp(result.get("created_at")).isoformat()
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API Error: {response.status} - {error_text}"
                    }

        except Exception as e:
            logger.error(f"Exception in create_custom_assistant: {str(e)}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }

    async def generate_response(self, 
                              assistant_id: str, 
                              prompt: str,
                              temperature: float = 0.7,
                              max_tokens: int = 1000) -> Dict:
        """
        Generate a response using a custom GPT assistant
        """
        try:
            # Create a thread
            thread_url = f"{self.base_url}/threads"
            thread_response = await self.session.post(thread_url, json={})
            thread_data = await thread_response.json()
            thread_id = thread_data.get("id")

            # Add message to thread
            message_url = f"{self.base_url}/threads/{thread_id}/messages"
            message_payload = {
                "role": "user",
                "content": prompt
            }
            await self.session.post(message_url, json=message_payload)

            # Run the assistant
            run_url = f"{self.base_url}/threads/{thread_id}/runs"
            run_payload = {
                "assistant_id": assistant_id,
                "instructions": "Please provide a helpful and accurate response.",
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            run_response = await self.session.post(run_url, json=run_payload)
            run_data = await run_response.json()
            run_id = run_data.get("id")

            # Wait for completion and get messages
            messages_url = f"{self.base_url}/threads/{thread_id}/messages"
            async with self.session.get(messages_url) as response:
                if response.status == 200:
                    messages = await response.json()
                    return {
                        "success": True,
                        "response": messages["data"][0]["content"][0]["text"],
                        "thread_id": thread_id,
                        "run_id": run_id
                    }
                else:
                    error_text = await response.text()
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

    async def list_assistants(self) -> Dict:
        """
        List all custom GPT assistants
        """
        try:
            url = f"{self.base_url}/assistants"
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "assistants": [{
                            "id": assistant["id"],
                            "name": assistant["name"],
                            "created_at": datetime.fromtimestamp(assistant["created_at"]).isoformat()
                        } for assistant in result.get("data", [])]
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
