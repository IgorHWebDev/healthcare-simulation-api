import pytest
import httpx
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, TimeoutException
import json
from datetime import datetime
from fastapi import FastAPI
from api.config.settings import settings

from api.main import app
from api.healthcare.ai_agent import HEALTHCARE_SYSTEM_PROMPT

# Create a test client
client = TestClient(app)

@pytest.fixture
def async_client():
    return TestClient(app)

@pytest.fixture
def mock_ollama_response():
    return {
        "model": "llama2",
        "created_at": "2024-03-21T12:00:00Z",
        "response": "This is a mock response from the Ollama API",
        "done": True
    }

@pytest.mark.asyncio
async def test_query_ollama_success(async_client, auth_headers):
    """Test successful query to Ollama API."""
    query_data = {
        "query": "What are the symptoms of COVID-19?",
        "model": settings.OLLAMA_MODEL,
        "temperature": 0.7
    }
    
    mock_response_data = {
        "response": "Common symptoms include fever, cough, and fatigue"
    }
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: mock_response_data
        mock_post.return_value = mock_response
        
        response = async_client.post(
            "/v1/healthcare/ai/query",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "confidence" in data
        assert "recommendations" in data
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_query_ollama_timeout(async_client, auth_headers):
    """Test handling of Ollama API timeout."""
    query_data = {
        "query": "What are the symptoms of COVID-19?",
        "model": settings.OLLAMA_MODEL,
        "temperature": 0.7
    }
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = TimeoutException("Request timed out")
        
        response = async_client.post(
            "/v1/healthcare/ai/query",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 503
        assert "timed out" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_process_healthcare_query_success(async_client, auth_headers):
    """Test successful processing of a healthcare query."""
    query_data = {
        "query": "What are the symptoms of COVID-19?",
        "model": "mistral",
        "temperature": 0.7
    }
    
    response = async_client.post(
        "/v1/healthcare/ai/process",
        json=query_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "confidence" in data
    assert "recommendations" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_process_healthcare_query_validation(async_client, auth_headers):
    """Test validation of healthcare query parameters."""
    query_data = {
        "query": "",  # Empty query
        "model": "mistral",
        "temperature": 0.7
    }
    
    response = async_client.post(
        "/v1/healthcare/ai/process",
        json=query_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_query_ollama_error_handling(async_client, auth_headers):
    """Test handling of Ollama API errors."""
    query_data = {
        "query": "What are the symptoms of COVID-19?",
        "model": settings.OLLAMA_MODEL,
        "temperature": 0.7
    }
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        response = async_client.post(
            "/v1/healthcare/ai/query",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_validate_healthcare_protocol(async_client, auth_headers):
    """Test validation of a healthcare protocol."""
    protocol_data = {
        "protocol": "COVID-19 Treatment Protocol",
        "parameters": {
            "severity": "mild",
            "age_group": "adult"
        },
        "guidelines": {
            "source": "WHO",
            "version": "2.0"
        }
    }
    
    response = async_client.post(
        "/v1/healthcare/ai/validate",
        json=protocol_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "validation_details" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_analyze_medical_data(async_client, auth_headers):
    """Test analysis of medical data."""
    analysis_data = {
        "data": {
            "blood_pressure": "120/80",
            "heart_rate": 75,
            "temperature": 37.0
        },
        "analysis_type": "vital_signs",
        "parameters": {
            "include_trends": True
        }
    }
    
    response = async_client.post(
        "/v1/healthcare/ai/analyze",
        json=analysis_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert "confidence" in data
    assert "recommendations" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_invalid_query(async_client, auth_headers):
    """Test handling of invalid query."""
    response = async_client.post(
        "/v1/healthcare/ai/query",
        json={"query": "", "model": settings.OLLAMA_MODEL, "temperature": 0.7},
        headers=auth_headers
    )
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_invalid_protocol(async_client, auth_headers):
    """Test handling of invalid protocol data."""
    response = async_client.post(
        "/v1/healthcare/ai/validate",
        json={},
        headers=auth_headers
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_invalid_analysis_data(async_client, auth_headers):
    """Test handling of invalid analysis data."""
    response = async_client.post(
        "/v1/healthcare/ai/analyze",
        json={},
        headers=auth_headers
    )
    assert response.status_code == 422

@pytest.mark.skip(reason="Ollama API not available")
@pytest.mark.asyncio
async def test_ollama_integration(async_client, auth_headers):
    """Test actual integration with Ollama API."""
    query_data = {
        "query": "What are the symptoms of COVID-19?",
        "model": settings.OLLAMA_MODEL,
        "temperature": 0.7
    }
    
    response = async_client.post(
        "/v1/healthcare/ai/query",
        json=query_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert len(data["analysis"]) > 0 