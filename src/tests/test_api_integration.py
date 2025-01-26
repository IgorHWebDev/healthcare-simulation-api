import pytest
import asyncio
from src.api.ollama_handler import OllamaHandler
from src.api.custom_gpt import CustomGPTHandler
import os
import json

@pytest.mark.asyncio
async def test_ollama_health():
    async with OllamaHandler() as handler:
        result = await handler.health_check()
        assert result["success"] == True
        assert result["status"] == 200

@pytest.mark.asyncio
async def test_ollama_models():
    async with OllamaHandler() as handler:
        result = await handler.list_models()
        assert result["success"] == True
        assert isinstance(result["models"], list)

@pytest.mark.asyncio
async def test_ollama_generation():
    async with OllamaHandler() as handler:
        result = await handler.generate_response(
            prompt="What is healthcare informatics?",
            model="llama2",
            temperature=0.7
        )
        assert result["success"] == True
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

@pytest.mark.asyncio
async def test_custom_gpt_creation():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OpenAI API key not found")
    
    async with CustomGPTHandler(api_key) as handler:
        result = await handler.create_custom_assistant(
            name="Healthcare Assistant",
            instructions="You are a healthcare informatics expert."
        )
        assert result["success"] == True
        assert "assistant_id" in result

@pytest.mark.asyncio
async def test_custom_gpt_response():
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    if not api_key or not assistant_id:
        pytest.skip("OpenAI credentials not found")
    
    async with CustomGPTHandler(api_key) as handler:
        result = await handler.generate_response(
            assistant_id=assistant_id,
            prompt="Explain the importance of FHIR in healthcare"
        )
        assert result["success"] == True
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

@pytest.mark.asyncio
async def test_integration_comparison():
    """
    Compare responses from both Ollama and Custom GPT
    """
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
    if not api_key or not assistant_id:
        pytest.skip("OpenAI credentials not found")
    
    test_prompt = "What are the key components of a healthcare information system?"
    
    async with OllamaHandler() as ollama, CustomGPTHandler(api_key) as custom_gpt:
        ollama_result = await ollama.generate_response(prompt=test_prompt)
        gpt_result = await custom_gpt.generate_response(
            assistant_id=assistant_id,
            prompt=test_prompt
        )
        
        assert ollama_result["success"] and gpt_result["success"]
        
        # Save responses for comparison
        with open("test_responses.json", "w") as f:
            json.dump({
                "ollama_response": ollama_result["response"],
                "gpt_response": gpt_result["response"]
            }, f, indent=2)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
